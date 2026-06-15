import os
import glob
import pandas as pd
import numpy as np


# -------------------------------------------------------------
# Configuration Paths
# If mounting on Kaggle, these paths usually look like:
# /kaggle/input/nih-chest-xrays/data/...
# /kaggle/input/covid19-radiography-database/COVID-19_Radiography_Dataset/...
# /kaggle/input/rsna-pneumonia-detection-challenge/...
# -------------------------------------------------------------
KAGGLE_INPUT_DIR = "/kaggle/input"  # Change this to "./dataset" for local testing

NIH_DIR = f"{KAGGLE_INPUT_DIR}/nih-chest-xrays/data"
COVID_DIR = f"{KAGGLE_INPUT_DIR}/covid19-radiography-database/COVID-19_Radiography_Dataset"
RSNA_DIR = f"{KAGGLE_INPUT_DIR}/rsna-pneumonia-detection-challenge"

# These are the 16 core diseases we will track.
# Anything not explicitly marked will be assumed 0 for that dataset.
DISEASES = [
    "Atelectasis", "Cardiomegaly", "Consolidation", "Edema", "Effusion",
    "Emphysema", "Fibrosis", "Hernia", "Infiltration", "Mass", "Nodule",
    "Pleural_Thickening", "Pneumonia", "Pneumothorax", "COVID-19", "Normal"
]


def load_nih_dataset() -> pd.DataFrame:
    """Load the NIH Chest X-ray14 Database metadata."""
    csv_path = os.path.join(NIH_DIR, "Data_Entry_2017.csv")
    if not os.path.exists(csv_path):
        print(f"Warning: NIH dataset not found at {csv_path}")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    
    # We need the absolute path to the images
    # NIH has images scattered in folders like "images_001/images"
    image_paths = {os.path.basename(p): p for p in glob.glob(f"{NIH_DIR}/images_*/images/*.png")}
    
    df['filepath'] = df['Image Index'].map(image_paths)
    df = df.dropna(subset=['filepath'])  # drop rows if image file wasn't found
    
    # Initialize all disease columns to 0
    for disease in DISEASES:
        df[disease] = 0
        
    # NIH labels look like "Cardiomegaly|Effusion".
    # If it says "No Finding", it's 'Normal'.
    for index, row in df.iterrows():
        labels = row['Finding Labels'].split('|')
        if "No Finding" in labels:
            df.at[index, 'Normal'] = 1
        else:
            for label in labels:
                if label in DISEASES:
                    df.at[index, label] = 1
                    
    # Only keep the columns we care about
    return df[['filepath'] + DISEASES]


def load_covid_dataset() -> pd.DataFrame:
    """Load the COVID-19 Radiography Database."""
    if not os.path.exists(COVID_DIR):
        print(f"Warning: COVID dataset not found at {COVID_DIR}")
        return pd.DataFrame()

    data = []
    
    # The folders in this dataset map directly to classes
    mapping = {
        "COVID": "COVID-19",
        "Normal": "Normal",
        "Viral Pneumonia": "Pneumonia",
        "Lung_Opacity": "Pneumonia"  # Often treated as a general pneumonia proxy
    }
    
    for folder, disease_label in mapping.items():
        folder_path = os.path.join(COVID_DIR, folder, "images")
        if not os.path.exists(folder_path):
            folder_path = os.path.join(COVID_DIR, folder) # Sometimes 'images' subfolder is missing
            
        images = glob.glob(f"{folder_path}/*.png")
        for img_path in images:
            row = {"filepath": img_path}
            for d in DISEASES:
                row[d] = 1 if d == disease_label else 0
            data.append(row)
            
    return pd.DataFrame(data)


def load_rsna_dataset() -> pd.DataFrame:
    """Load the RSNA Pneumonia Database."""
    csv_path = os.path.join(RSNA_DIR, "stage_2_train_labels.csv")
    if not os.path.exists(csv_path):
        print(f"Warning: RSNA dataset not found at {csv_path}")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    
    # Drop duplicates because RSNA has multiple bounding boxes per image
    df = df.drop_duplicates(subset=['patientId'])
    
    # Construct DICOM file paths
    df['filepath'] = df['patientId'].apply(lambda x: os.path.join(RSNA_DIR, "stage_2_train_images", f"{x}.dcm"))
    
    # Note: RSNA images are in .dcm (DICOM) format. 
    # Your ImageDataGenerator will need a custom loader to read .dcm, or you must pre-convert them to .png.
    
    for disease in DISEASES:
        df[disease] = 0
        
    df['Pneumonia'] = df['Target']
    df['Normal'] = (df['Target'] == 0).astype(int) # If Target is 0, we assume Normal (or non-pneumonia)
    
    return df[['filepath'] + DISEASES]


def build_master_dataframe() -> pd.DataFrame:
    """Merges all datasets into a single massive dataframe."""
    print("Loading NIH Chest X-ray14...")
    nih_df = load_nih_dataset()
    print(f"  -> Found {len(nih_df)} images.")
    
    print("Loading COVID-19 Radiography...")
    covid_df = load_covid_dataset()
    print(f"  -> Found {len(covid_df)} images.")
    
    print("Loading RSNA Pneumonia...")
    rsna_df = load_rsna_dataset()
    print(f"  -> Found {len(rsna_df)} images.")
    
    # Combine them all
    master_df = pd.concat([nih_df, covid_df, rsna_df], ignore_index=True)
    
    print(f"\nTotal combined medical images: {len(master_df)}")
    return master_df

if __name__ == "__main__":
    df = build_master_dataframe()
    if len(df) > 0:
        print("\nSample Data:")
        print(df.head())
        
        # Save to CSV so train.py can just read this single file
        output_path = "master_kaggle_metadata.csv"
        df.to_csv(output_path, index=False)
        print(f"\nSaved combined metadata to {output_path}")
