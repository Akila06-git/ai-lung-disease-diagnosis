from __future__ import annotations

"""Training script for the lung disease detection model.

This script expects datasets downloaded from Kaggle:

- COVID-19 Radiography Database:
  https://www.kaggle.com/tawsifurrahman/covid19-radiography-database
- TB Chest X-ray Database:
  https://www.kaggle.com/tawsifurrahman/tuberculosis-tb-chest-xray-dataset

Place the extracted folders under: ``backend/dataset/``.

The script:
 - Combines datasets into a unified folder structure.
 - Applies data augmentation.
 - Handles class imbalance via class weights.
 - Splits into 70% train, 15% validation, 15% test.
 - Uses MobileNetV2 transfer learning (see model.py).
 - Trains in two phases: head-only then fine-tuning.
 - Saves best model to ``ml_model/saved_models/model.h5``.
"""

import json
import os
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau,
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from .model import create_model, compile_model, IMAGE_SIZE


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
COMBINED_DIR = DATASET_DIR / "combined"
SAVED_MODELS_DIR = Path(__file__).resolve().parent / "saved_models"
SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)


CLASSES = [
    "COVID-19",
    "Tuberculosis",
    "Bacterial Pneumonia",
    "Viral Pneumonia",
    "Normal",
]


def prepare_combined_dataset() -> None:
    """Prepare a combined dataset directory with class subfolders.

    This function assumes you have manually placed images into subfolders for
    the COVID and TB datasets. To keep this script environment-agnostic, we
    avoid moving files automatically and instead document the expected layout:

    backend/dataset/combined/
        COVID-19/
        Tuberculosis/
        Bacterial Pneumonia/
        Viral Pneumonia/
        Normal/
    """
    COMBINED_DIR.mkdir(parents=True, exist_ok=True)
    for cls in CLASSES:
        (COMBINED_DIR / cls).mkdir(parents=True, exist_ok=True)


def build_generators(
    dataframe: "pandas.DataFrame",
    directory: str,
    x_col: str,
    y_cols: list[str],
    image_size: Tuple[int, int] = IMAGE_SIZE,
    batch_size: int = 32,
) -> Tuple[tf.keras.preprocessing.image.DataFrameIterator, ...]:
    """Create train, validation, and test generators for multi-label classification from a DataFrame.
    
    Args:
        dataframe: Pandas DataFrame containing the dataset metadata.
        directory: The base path where the images are stored.
        x_col: The column name containing the image filenames.
        y_cols: A list of column names for the binary disease labels.
    """
    import pandas as pd
    from sklearn.model_selection import train_test_split

    # Split the DataFrame 70/15/15
    # NOTE: In a real medical scenario, this split SHOULD be grouped by Patient ID
    # to prevent data leakage.
    train_df, temp_df = train_test_split(dataframe, test_size=0.30, random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42)

    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
    )

    # For validation/test (no augmentation, only rescaling)
    test_datagen = ImageDataGenerator(rescale=1.0 / 255.0)

    train_generator = train_datagen.flow_from_dataframe(
        dataframe=train_df,
        directory=directory,
        x_col=x_col,
        y_col=y_cols,
        target_size=image_size,
        batch_size=batch_size,
        class_mode="raw", # Use 'raw' for multi-label binary arrays
        shuffle=True,
    )

    val_generator = test_datagen.flow_from_dataframe(
        dataframe=val_df,
        directory=directory,
        x_col=x_col,
        y_col=y_cols,
        target_size=image_size,
        batch_size=batch_size,
        class_mode="raw",
        shuffle=False,
    )

    test_generator = test_datagen.flow_from_dataframe(
        dataframe=test_df,
        directory=directory,
        x_col=x_col,
        y_col=y_cols,
        target_size=image_size,
        batch_size=batch_size,
        class_mode="raw",
        shuffle=False,
    )

    return train_generator, val_generator, test_generator


def compute_class_weights_from_generator(
    generator: tf.keras.preprocessing.image.DataFrameIterator,
) -> Dict[int, float]:
    """Compute class weights to handle imbalance for multi-label data.
    
    Since each row can have multiple labels, we compute weights per binary class.
    """
    import numpy as np
    y = generator.labels
    weights = {}
    num_samples = len(y)
    num_classes = y.shape[1]
    
    for i in range(num_classes):
        positives = np.sum(y[:, i])
        negatives = num_samples - positives
        # Simple heuristic: heavily weight the minority (often the positive case)
        if positives == 0:
             weights[i] = 1.0 # prevent division by zero
        else:
            weights[i] = num_samples / (2.0 * positives)
            
    return weights


def main() -> None:
    import pandas as pd
    import os
    
    batch_size = 32
    
    # -------------------------------------------------------------
    # KAGGLE MERGE LOGIC PLACEHOLDER
    # -------------------------------------------------------------
    # In a real Kaggle notebook, you would load all your CSVs, 
    # harmonize them, and create `master_df` here.
    # For now, we will create a dummy dataframe if run locally 
    # just to ensure the pipeline doesn't crash during debugging.
    
    print("WARNING: Building a dummy dataframe for local testing.")
    print("On Kaggle, you must replace this with your actual merged DataFrame.")
    
    # Let's assume you have an 'images' folder for testing
    dummy_images_dir = str(COMBINED_DIR)
    
    # Let's pretend we have 3 diseases
    y_cols = ["COVID-19", "Pneumonia", "Normal"]
    
    # Simulate some image files if none exist for pipeline testing
    dummy_data = []
    if os.path.exists(dummy_images_dir):
        # Just grab random files from the old directory structure for testing flow
        for root, dirs, files in os.walk(dummy_images_dir):
            for file in files:
                if file.endswith((".png", ".jpg", ".jpeg")):
                    dummy_data.append({
                        "filename": os.path.relpath(os.path.join(root, file), dummy_images_dir),
                        "COVID-19": np.random.choice([0, 1]),
                        "Pneumonia": np.random.choice([0, 1]),
                        "Normal": np.random.choice([0, 1])
                    })
    
    if not dummy_data:
        # Create a completely fake entry so pandas doesn't crash if dir is empty
        dummy_data = [{"filename": "fake_image.jpg", "COVID-19": 0, "Pneumonia": 0, "Normal": 1}]
        
    master_df = pd.DataFrame(dummy_data)
    
    # -------------------------------------------------------------

    train_gen, val_gen, test_gen = build_generators(
        dataframe=master_df,
        directory=dummy_images_dir,
        x_col="filename",
        y_cols=y_cols,
        batch_size=batch_size
    )

    num_classes = len(y_cols)
    print(f"Detected classes: {y_cols}")

    # For multi-label, Keras handles class weights differently, 
    # you often have to pass them as a dictionary if using `class_weight` arg
    # but since we're using Binary Crossentropy, computing them per output node
    class_weights = compute_class_weights_from_generator(train_gen)
    
    with open(SAVED_MODELS_DIR / "class_weights.json", "w", encoding="utf-8") as f:
        json.dump(class_weights, f)

    model = create_model(num_classes=num_classes)
    model = compile_model(model, base_learning_rate=1e-4)

    callbacks = [
        ModelCheckpoint(
            filepath=str(SAVED_MODELS_DIR / "model.h5"),
            monitor="val_auc", # Watch AUC instead of accuracy for multi-label
            save_best_only=True,
            save_weights_only=False,
            mode="max",
            verbose=1,
        ),
        EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    # Phase 1: train top layers with base frozen
    history1 = model.fit(
        train_gen,
        epochs=15,
        validation_data=val_gen,
        class_weight=class_weights,
        callbacks=callbacks,
    )

    # Phase 2: fine-tune some of the base_model layers
    base_model = model.get_layer("densenet121")
    base_model.trainable = True
    fine_tune_at = len(base_model.layers) // 2
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False

    model = compile_model(model, base_learning_rate=1e-5)

    history2 = model.fit(
        train_gen,
        epochs=30,
        validation_data=val_gen,
        class_weight=class_weights,
        callbacks=callbacks,
    )

    # Evaluate on test set
    print("Evaluating on test set...")
    test_metrics = model.evaluate(test_gen)
    print(f"Test Metrics: {dict(zip(model.metrics_names, test_metrics))}")


if __name__ == "__main__":
    main()

