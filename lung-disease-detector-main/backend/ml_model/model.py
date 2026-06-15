from __future__ import annotations

from typing import Tuple

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers


IMAGE_SIZE: Tuple[int, int] = (224, 224)


def get_data_augmentation() -> tf.keras.Sequential:
    """Return a data augmentation pipeline."""
    return tf.keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.1),
            layers.RandomZoom(0.1),
        ],
        name="data_augmentation",
    )


class DenseNetPreprocess(layers.Layer):
    """Applies DenseNet121 preprocessing inside the model.
    Using a proper Keras layer instead of Lambda avoids the safe_mode
    deserialization error when loading the model in Django on Windows.
    """
    def call(self, x):
        return tf.keras.applications.densenet.preprocess_input(x)

    def get_config(self):
        return super().get_config()

def create_model(num_classes: int) -> tf.keras.Model:
    base_model = tf.keras.applications.DenseNet121(
        input_shape=(*IMAGE_SIZE, 3), include_top=False, weights="imagenet"
    )
    base_model.trainable = False

    inputs = layers.Input(shape=(*IMAGE_SIZE, 3))
    x = layers.RandomFlip("horizontal")(inputs, training=True)
    x = layers.RandomRotation(0.08)(x, training=True)
    x = layers.Rescaling(255.0)(x)
    x = DenseNetPreprocess()(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(512, activation="relu")(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    return models.Model(inputs, outputs, name="lung_disease_8class")


def compile_model(model: tf.keras.Model, base_learning_rate: float = 1e-4) -> tf.keras.Model:
    optimizer = optimizers.Adam(learning_rate=base_learning_rate)
    
    model.compile(
        optimizer=optimizer,
        loss="categorical_crossentropy", 
        metrics=[
            "accuracy",
            tf.keras.metrics.AUC(name="auc"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ]
    )
    return model

