import sys
import os
import numpy as np
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import tensorflow as tf
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_model.predict import get_model, preprocess_image

CLASS_NAMES = [
    "Normal", "Edema", "Pneumothorax",
    "Pneumonia-Bacterial", "Pneumonia-Viral", "COVID-19",
    "Tuberculosis", "Emphysema"
]

# Path to the image you tested
test_images = [
    r"C:\Users\acer\Downloads\COVID-1.png",
    r"C:\Users\acer\Downloads\Tuberculosis-660.png",
    r"C:\Users\acer\Downloads\Pneumonia-Bacterial (1014).jpg"
]

def run_diagnostic():
    for test_image in test_images:
        print("\n" + "=" * 50)
        if not os.path.exists(test_image):
            print(f"Error: {test_image} not found. Please ensure the file is in your Downloads.")
            continue

        print(f"--- FULL PROBABILITY SCAN: {os.path.basename(test_image)} ---")
        try:
            model = get_model()
            arr = preprocess_image(test_image)
            preds = model.predict(arr, verbose=0)[0]
            
            # Sort all 8 classes by probability
            results = []
            for i in range(len(CLASS_NAMES)):
                results.append((CLASS_NAMES[i], preds[i]))
            
            results.sort(key=lambda x: x[1], reverse=True)
            
            print(f"{'Disease':<20} | {'Probability':<12}")
            print("-" * 35)
            for name, prob in results:
                indicator = " <--" if prob > 0.2 else ""
                print(f"{name:<20} | {prob*100:>10.2f}%{indicator}")
                
        except Exception as e:
            print(f"Diagnostic failed: {e}")

if __name__ == "__main__":
    run_diagnostic()
