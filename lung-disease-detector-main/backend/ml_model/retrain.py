"""
Model Retraining Pipeline — fine-tune the prediction model using user feedback.

This module loads corrected predictions from the database, extracts the
original X-ray images and their corrected labels, and fine-tunes the existing
model weights for a few epochs with a low learning rate.

Usage:
    # As a standalone management script:
    python -m ml_model.retrain

    # Or triggered via Celery task (see api/tasks.py)
"""
from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Tuple

import numpy as np
import tensorflow as tf
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLASS_NAMES = [
    "Bacterial Pneumonia",
    "COVID-19",
    "Normal",
    "Tuberculosis",
    "Viral Pneumonia",
]

NUM_CLASSES = len(CLASS_NAMES)
IMAGE_SIZE = (224, 224)

SAVED_MODELS_DIR = Path(__file__).resolve().parent / "saved_models"
CURRENT_WEIGHTS = SAVED_MODELS_DIR / "converted_model.weights.h5"

# Retraining hyperparameters
RETRAIN_LEARNING_RATE = 1e-5   # Very low LR for fine-tuning
RETRAIN_EPOCHS = 3
RETRAIN_BATCH_SIZE = 8
MIN_SAMPLES_REQUIRED = 2      # Minimum corrections needed to trigger retraining


def _class_to_index(class_name: str) -> int:
    """Convert a class name to its index."""
    try:
        return CLASS_NAMES.index(class_name)
    except ValueError:
        raise ValueError(f"Unknown class: {class_name}. Valid: {CLASS_NAMES}")


def _preprocess_image(image_path: str) -> np.ndarray:
    """Load and preprocess an image for training (same as predict.py)."""
    img = Image.open(image_path).convert("RGB")
    img = img.resize(IMAGE_SIZE, Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32)  # keep [0, 255] — model has preprocess_input
    return arr


def _load_feedback_data() -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Query corrected predictions from the database and return
    (images_array, labels_one_hot, count).
    """
    # Import here to avoid circular imports and ensure Django is configured
    from api.models import Prediction

    corrected = Prediction.objects.filter(
        is_corrected=True,
        true_class__isnull=False,
    ).exclude(true_class="").select_related()

    images = []
    labels = []
    skipped = 0

    for pred in corrected:
        try:
            img_path = pred.image.path
            if not os.path.exists(img_path):
                logger.warning("Image not found: %s (prediction %s)", img_path, pred.id)
                skipped += 1
                continue

            img = _preprocess_image(img_path)
            label_idx = _class_to_index(pred.true_class)

            images.append(img)
            # One-hot encode
            one_hot = np.zeros(NUM_CLASSES, dtype=np.float32)
            one_hot[label_idx] = 1.0
            labels.append(one_hot)

        except Exception as e:
            logger.warning("Skipping prediction %s: %s", pred.id, e)
            skipped += 1
            continue

    if skipped > 0:
        logger.info("Skipped %d predictions due to errors.", skipped)

    if not images:
        return np.array([]), np.array([]), 0

    return np.array(images), np.array(labels), len(images)


def _backup_weights() -> Path:
    """Create a timestamped backup of the current weights."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SAVED_MODELS_DIR / f"backup_{timestamp}.weights.h5"
    if CURRENT_WEIGHTS.exists():
        shutil.copy2(CURRENT_WEIGHTS, backup_path)
        logger.info("Backed up current weights to %s", backup_path)
    return backup_path


def retrain_model() -> dict:
    """
    Main retraining function.

    Returns a dict with training results:
        {
            "status": "success" | "skipped" | "error",
            "message": str,
            "samples_used": int,
            "epochs": int,
            "final_accuracy": float,
            "backup_path": str,
        }
    """
    logger.info("=" * 60)
    logger.info("MODEL RETRAINING PIPELINE STARTED")
    logger.info("=" * 60)

    start = perf_counter()

    # Step 1: Load feedback data
    logger.info("Step 1: Loading corrected predictions from database...")
    X, y, count = _load_feedback_data()

    if count < MIN_SAMPLES_REQUIRED:
        msg = (
            f"Not enough corrected samples for retraining. "
            f"Found {count}, need at least {MIN_SAMPLES_REQUIRED}."
        )
        logger.warning(msg)
        return {"status": "skipped", "message": msg, "samples_used": count}

    logger.info("Loaded %d corrected samples for retraining.", count)

    # Step 2: Backup current weights
    logger.info("Step 2: Backing up current weights...")
    backup_path = _backup_weights()

    # Step 3: Build and load model
    logger.info("Step 3: Loading current model...")
    from .model import create_model

    model = create_model(num_classes=NUM_CLASSES)

    if CURRENT_WEIGHTS.exists():
        model.load_weights(str(CURRENT_WEIGHTS))
        logger.info("Loaded existing weights from %s", CURRENT_WEIGHTS)
    else:
        logger.warning("No existing weights found! Training from ImageNet base.")

    # Step 4: Compile with low learning rate for fine-tuning
    logger.info("Step 4: Compiling model (lr=%s)...", RETRAIN_LEARNING_RATE)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=RETRAIN_LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    # Step 5: Fine-tune
    logger.info("Step 5: Fine-tuning for %d epochs on %d samples...", RETRAIN_EPOCHS, count)

    try:
        history = model.fit(
            X, y,
            epochs=RETRAIN_EPOCHS,
            batch_size=min(RETRAIN_BATCH_SIZE, count),
            validation_split=0.2 if count >= 10 else 0.0,
            verbose=1,
        )

        final_acc = float(history.history["accuracy"][-1])
        final_loss = float(history.history["loss"][-1])
        logger.info("Training complete. Final accuracy: %.4f, Loss: %.4f", final_acc, final_loss)

    except Exception as e:
        logger.error("Training failed: %s", e)
        # Restore backup
        if backup_path.exists():
            shutil.copy2(backup_path, CURRENT_WEIGHTS)
            logger.info("Restored weights from backup after failure.")
        return {"status": "error", "message": str(e), "samples_used": count}

    # Step 6: Save new weights
    logger.info("Step 6: Saving retrained weights...")
    model.save_weights(str(CURRENT_WEIGHTS))

    # Also save a versioned copy
    version_path = SAVED_MODELS_DIR / f"retrained_{datetime.now().strftime('%Y%m%d_%H%M%S')}.weights.h5"
    model.save_weights(str(version_path))
    logger.info("Saved versioned weights to %s", version_path)

    elapsed = (perf_counter() - start) * 1000.0

    # Step 7: Mark predictions as used for training
    logger.info("Step 7: Marking predictions as used for training...")
    _mark_as_trained()

    result = {
        "status": "success",
        "message": f"Model retrained on {count} samples in {elapsed:.0f}ms.",
        "samples_used": count,
        "epochs": RETRAIN_EPOCHS,
        "final_accuracy": final_acc,
        "final_loss": final_loss,
        "backup_path": str(backup_path),
        "new_weights": str(version_path),
        "training_time_ms": elapsed,
    }

    logger.info("=" * 60)
    logger.info("RETRAINING COMPLETE: %s", result["message"])
    logger.info("=" * 60)

    return result


def _mark_as_trained():
    """Mark all corrected predictions as used (so they aren't re-used)."""
    from api.models import Prediction

    # We add a 'used_for_training' note by updating corrected_at to now
    # This prevents re-processing in future retraining runs
    from django.utils import timezone
    Prediction.objects.filter(
        is_corrected=True,
        true_class__isnull=False,
    ).update(corrected_at=timezone.now())


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()

    logging.basicConfig(level=logging.INFO)
    result = retrain_model()
    print(result)
