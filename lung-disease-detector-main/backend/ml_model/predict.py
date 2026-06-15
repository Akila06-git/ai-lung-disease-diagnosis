from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from time import perf_counter
from typing import Tuple

import numpy as np
import tensorflow as tf
from PIL import Image

from .model import IMAGE_SIZE, create_model, compile_model


logger = logging.getLogger(__name__)

_model: tf.keras.Model | None = None
_model_lock = threading.Lock()

NUM_CLASSES = 8 


def _load_model() -> None:
    global _model

    default_path = str(
        Path(__file__).resolve().parent / "saved_models" / "model.keras"
    )
    model_path = os.getenv("MODEL_PATH", default_path)
    logger.info("Loading ML model from %s", model_path)
    start = perf_counter()

    # Build architecture locally, then load only weights from the .keras file
    # This avoids the Lambda layer deserialization deadlock on Windows/Keras 3.x
    model = compile_model(create_model(NUM_CLASSES))
    model.load_weights(model_path)

    _model = model
    elapsed = (perf_counter() - start) * 1000
    logger.info("Model loaded in %.2f ms", elapsed)

def get_model() -> tf.keras.Model:
    """Return the global model instance, loading it once with double-checked locking."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _load_model()
    assert _model is not None
    return _model


def reload_model() -> None:
    """Force-reload the model from disk (e.g. after retraining).

    Thread-safe: acquires the model lock before clearing the cached instance.
    The next call to ``get_model()`` will load the updated weights.
    """
    global _model
    with _model_lock:
        _model = None
    logger.info("Model cache cleared — next prediction will load fresh weights.")


def preprocess_image(image_path: str) -> np.ndarray:
    """Load and preprocess an image file for DenseNet121 prediction.
    """
    img = Image.open(image_path).convert("RGB")
    img = img.resize(IMAGE_SIZE, Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) 
    arr = np.expand_dims(arr, axis=0) # shape (1, 224, 224, 3), values [0, 255]
    
    # Preprocessing natively handled by the model's new DenseNetPreprocess layer
    arr = arr / 255.0 # Feed [0, 1] to the Rescaling(255.0) layer in the model
    return arr

THRESHOLD = 0.5

def predict_image(image_path: str, class_names: list[str]) -> Tuple[str, float, float]:
    model = get_model()
    inputs = preprocess_image(image_path)

    start = perf_counter()
    preds = model.predict(inputs, verbose=0)
    elapsed_ms = (perf_counter() - start) * 1000.0

    probs = preds[0]  # shape: (8,)
    
    # Softmax output: pick highest probability automatically
    idx = int(np.argmax(probs))
    predicted_class = class_names[idx]
    confidence = float(probs[idx])

    # Show all detected for logging, sorted
    detected = [(class_names[i], float(probs[i])) for i in range(len(class_names))]
    detected.sort(key=lambda x: x[1], reverse=True)

    logger.info(
        "Prediction: %s (%.2f%%) in %.2f ms | All detected: %s",
        predicted_class, confidence * 100.0, elapsed_ms,
        [(c, f"{p*100:.1f}%") for c, p in detected]
    )
    return predicted_class, confidence, elapsed_ms