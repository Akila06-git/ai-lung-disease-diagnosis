import os
from pathlib import Path

# Define base directory
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
COMBINED_DIR = DATASET_DIR / "combined"

# Define classes
CLASSES = [
    "COVID-19",
    "Tuberculosis",
    "Bacterial Pneumonia",
    "Viral Pneumonia",
    "Normal",
]

def create_dirs():
    print(f"Creating directories under: {COMBINED_DIR}")
    COMBINED_DIR.mkdir(parents=True, exist_ok=True)
    
    for cls in CLASSES:
        cls_dir = COMBINED_DIR / cls
        cls_dir.mkdir(parents=True, exist_ok=True)
        print(f"  - Created: {cls_dir}")

if __name__ == "__main__":
    create_dirs()
