"""
Grad-CAM (Gradient-weighted Class Activation Mapping) for the DenseNet121 model.

Generates visual explanations of AI predictions by highlighting regions
of the X-ray that most influenced the classification decision.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image

from .model import IMAGE_SIZE
from .predict import get_model, preprocess_image

logger = logging.getLogger(__name__)

# The last convolutional layer in DenseNet121
GRAD_CAM_LAYER = "conv5_block16_2_conv"


def generate_gradcam_heatmap(
    image_path: str,
    predicted_class_index: int,
) -> np.ndarray:
    """Generate a Grad-CAM heatmap by transferring weights to a clean model.
    This bypasses Keras 3 nesting issues that break standard functional graph tracing.
    """
    model = get_model()

    # Access the nested base model
    try:
        base_model = model.get_layer("densenet121")
    except ValueError:
        logger.error("Could not find 'densenet121' layer.")
        raise

    # 1. Create a FRESH DenseNet121 model with the same architecture
    # This ensures a clean, non-nested functional graph
    clean_base = tf.keras.applications.DenseNet121(
        include_top=False, weights=None, input_shape=(224, 224, 3)
    )
    # 2. Transfer weights from the model's densenet layer
    clean_base.set_weights(base_model.get_weights())

    # 3. Create the grad model for the clean base
    target_layer = clean_base.get_layer(GRAD_CAM_LAYER)
    sub_grad_model = tf.keras.Model(
        inputs=clean_base.input,
        outputs=[target_layer.output, clean_base.output]
    )

    # Preprocess initial image (resize/standardize)
    img_array = preprocess_image(image_path)
    
    # Run through essential preprocessing layers (skip augmentation)
    try:
        img_array = model.get_layer("rescaling")(img_array)
        img_array = model.get_layer("dense_net_preprocess")(img_array)
    except Exception as e:
        logger.warning("Preprocessing layers failed, using raw: %s", e)

    # Track gradients
    classifier_layers = model.layers[model.layers.index(base_model)+1:]
    
    with tf.GradientTape() as tape:
        conv_outputs, base_output = sub_grad_model(img_array, training=False)
        tape.watch(conv_outputs)
        
        # Manually chain the final classifier layers
        x = base_output
        for layer in classifier_layers:
            try:
                x = layer(x, training=False)
            except (TypeError, ValueError):
                x = layer(x)
        
        class_output = x[:, predicted_class_index]

    # Compute gradients and normalize heatmap
    grads = tape.gradient(class_output, conv_outputs)
    if grads is None:
        raise ValueError("Gradient tracking failed on clean model.")

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy()


def create_gradcam_overlay(
    image_path: str,
    predicted_class_index: int,
    alpha: float = 0.4,
) -> io.BytesIO:
    """Create a Grad-CAM overlay image combining the heatmap with the original.

    Args:
        image_path: Path to the original X-ray image.
        predicted_class_index: Index of the predicted class.
        alpha: Transparency of the heatmap overlay (0=transparent, 1=opaque).

    Returns:
        A BytesIO object containing the overlay as a JPEG image.
    """
    # Generate heatmap
    heatmap = generate_gradcam_heatmap(image_path, predicted_class_index)

    # Load the original image
    original = cv2.imread(image_path)
    if original is None:
        raise ValueError(f"Could not read image: {image_path}")

    original = cv2.resize(original, (IMAGE_SIZE[0], IMAGE_SIZE[1]))

    # Resize heatmap to match original image dimensions
    heatmap_resized = cv2.resize(heatmap, (original.shape[1], original.shape[0]))
    heatmap_colored = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_colored, cv2.COLORMAP_JET)

    # Superimpose the heatmap on the original image
    overlay = cv2.addWeighted(original, 1 - alpha, heatmap_colored, alpha, 0)

    # Convert BGR to RGB for PIL
    overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
    overlay_img = Image.fromarray(overlay_rgb)

    # Save to BytesIO
    buffer = io.BytesIO()
    overlay_img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    logger.info("Grad-CAM overlay generated for %s (class idx %d)", image_path, predicted_class_index)
    return buffer
