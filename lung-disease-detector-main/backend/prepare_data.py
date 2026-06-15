import kagglehub
import shutil
import os
from pathlib import Path
import glob

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
COMBINED_DIR = DATASET_DIR / "combined"

def setup_dirs():
    """Create necessary directories."""
    print(f"Creating directories in {COMBINED_DIR}...")
    COMBINED_DIR.mkdir(parents=True, exist_ok=True)
    
    classes = [
        "COVID-19",
        "Tuberculosis",
        "Bacterial Pneumonia",
        "Viral Pneumonia",
        "Normal",
    ]
    for cls in classes:
        (COMBINED_DIR / cls).mkdir(parents=True, exist_ok=True)
    print("Directories created.")

def copy_images(src_dir, dest_dir):
    """Copy images from source to destination, handling 'images' subdir."""
    
    # Check if 'images' subdir exists
    src_path = Path(src_dir)
    if (src_path / "images").exists():
        src_path = src_path / "images"
    
    print(f"Copying from {src_path} to {dest_dir}...")
    
    files = glob.glob(f"{src_path}/*.png") + glob.glob(f"{src_path}/*.jpg") + glob.glob(f"{src_path}/*.jpeg")
    
    if not files:
        print(f"WARNING: No images found in {src_path}")
        return

    count = 0
    for f in files:
        try:
            shutil.copy(f, dest_dir)
            count += 1
        except Exception as e:
            print(f"Error copying {f}: {e}")
            
    print(f"  -> Copied {count} images.")

    print(f"  -> Copied {count} images.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Prepare dataset for training.")
    parser.add_argument("--covid_path", type=str, help="Path to manually downloaded COVID-19 Radiography Database", default=None)
    parser.add_argument("--tb_path", type=str, help="Path to manually downloaded TB Chest X-ray Database", default=None)
    args = parser.parse_args()

    setup_dirs()
    
    # --- COVID-19 DATASET ---
    if args.covid_path:
        print(f"\n--- Using Local COVID-19 Database: {args.covid_path} ---")
        covid_path = args.covid_path
    else:
        print("\n--- Downloading COVID-19 Radiography Database ---")
        try:
            covid_path = kagglehub.dataset_download("tawsifurrahman/covid19-radiography-database")
            print(f"Downloaded to: {covid_path}")
        except Exception as e:
            print(f"Error downloading COVID dataset: {e}")
            print("Tip: Ensure you have your Kaggle API key set up (kaggle.json).")
            return

    print("\nProcessing COVID-19 Data...")
    
    # 1. COVID-19
    copy_images(
        src_dir=os.path.join(covid_path, "COVID-19_Radiography_Dataset", "COVID"),
        dest_dir=COMBINED_DIR / "COVID-19"
    )
    
    # 2. Viral Pneumonia
    copy_images(
        src_dir=os.path.join(covid_path, "COVID-19_Radiography_Dataset", "Viral Pneumonia"),
        dest_dir=COMBINED_DIR / "Viral Pneumonia"
    )
    
    # 3. Bacterial Pneumonia (Lung_Opacity)
    copy_images(
        src_dir=os.path.join(covid_path, "COVID-19_Radiography_Dataset", "Lung_Opacity"),
        dest_dir=COMBINED_DIR / "Bacterial Pneumonia"
    )
    
    # 4. Normal (Part 1)
    copy_images(
        src_dir=os.path.join(covid_path, "COVID-19_Radiography_Dataset", "Normal"),
        dest_dir=COMBINED_DIR / "Normal"
    )

    # --- TUBERCULOSIS DATASET ---
    if args.tb_path:
        print(f"\n--- Using Local TB Database: {args.tb_path} ---")
        tb_path = args.tb_path
    else:
        print("\n--- Downloading Tuberculosis TB Chest X-ray Database ---")
        try:
            tb_path = kagglehub.dataset_download("tawsifurrahman/tuberculosis-tb-chest-xray-dataset")
            print(f"Downloaded to: {tb_path}")
        except Exception as e:
            print(f"Error downloading TB dataset: {e}")
            return
    
    print("\nProcessing Tuberculosis Data...")
    
    # 5. Tuberculosis
    copy_images(
        src_dir=os.path.join(tb_path, "TB_Chest_Radiography_Database", "Tuberculosis"),
        dest_dir=COMBINED_DIR / "Tuberculosis"
    )
    
    # 6. Normal (Part 2 - Optional, add more normal images)
    copy_images(
        src_dir=os.path.join(tb_path, "TB_Chest_Radiography_Database", "Normal"),
        dest_dir=COMBINED_DIR / "Normal"
    )

    print("\n--- Dataset Preparation Complete! ---")
    print(f"Data is ready in: {COMBINED_DIR}")
    print("You can now run 'python ml_model/train.py'")

if __name__ == "__main__":
    main()
