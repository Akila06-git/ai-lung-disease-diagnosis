import sys
import os
import numpy as np
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import tensorflow as tf
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_model.predict import get_model, preprocess_image

CLASS_NAMES = [
    "Atelectasis", "Cardiomegaly", "Consolidation", "Edema", "Effusion",
    "Emphysema", "Fibrosis", "Hernia", "Infiltration", "Mass", "Nodule",
    "Pleural_Thickening", "Pneumonia", "Pneumothorax", "COVID-19", "Tuberculosis", "Normal"
]

# Use the benchmark images the user just downloaded
test_images = [
    r"C:\Users\acer\Downloads\00000001_000.png", # Cardiomegaly
    r"C:\Users\acer\Downloads\00000003_000.png", # Hernia
    r"C:\Users\acer\Downloads\00000009_000.png"  # Emphysema
]

print("--- NEW MODEL DIRECT INFERENCE TEST ---")
for img_path in test_images:
    if os.path.exists(img_path):
        print(f"\nTesting {img_path}...")
        try:
            arr = preprocess_image(img_path)
            model = get_model()
            preds = model.predict(arr, verbose=0)[0]
            
            top_3 = np.argsort(preds)[-3:][::-1]
            for idx in top_3:
                print(f"  {CLASS_NAMES[idx]}: {preds[idx]*100:.2f}%")
        except Exception as e:
            print(f"Error testing: {e}")
    else:
        print(f"Skipping {img_path} - file not found locally")
