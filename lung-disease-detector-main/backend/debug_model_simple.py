
import os
import sys
import numpy as np
import tensorflow as tf

# Add /app to python path
sys.path.append("/app")

from ml_model.predict import get_model, preprocess_image

def debug_model():
    print("Loading model...")
    model = get_model()
    print(f"Model loaded. Output shape: {model.output_shape}")
    

    # Load actual image
    image_path = "/app/media/xray_images/6601402048ec48a59e4230fb3ca78810.png"
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found")
        return

    CLASS_NAMES = [
        "Bacterial Pneumonia",
        "COVID-19",
        "Normal",
        "Tuberculosis",
        "Viral Pneumonia",
    ]

    print(f"Calling predict_image for {image_path}...")
    from ml_model.predict import predict_image
    
    predicted_class, confidence, time_ms = predict_image(image_path, CLASS_NAMES)
    
    print(f"Result: Class={predicted_class}, Conf={confidence:.4f}, Time={time_ms:.2f}ms")

if __name__ == "__main__":
    debug_model()
