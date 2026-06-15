import os
import glob
import sys
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from sklearn.model_selection import GroupShuffleSplit

# ==============================================================================
# 1. PATHS
# ==============================================================================
CHEXPERT_DIR    = "/kaggle/input/datasets/willarevalo/chexpert-v10-small/CheXpert-v1.0-small"
CHESTX6_DIR     = "/kaggle/input/datasets/mohamedasak/chest-x-ray-6-classes-dataset/chest-xray"
COVIDQU_DIR     = "/kaggle/input/datasets/anasmohammedtahir/covidqu/Lung Segmentation Data/Lung Segmentation Data"
CHEXNET_WEIGHTS = "/kaggle/input/datasets/sinamhd9/chexnet-weights/brucechou1983_CheXNet_Keras_0.3.0_weights.h5"

# ==============================================================================
# 2. DIRECTORY CHECK
# ==============================================================================
print("=" * 60)
print("Checking dataset directories...")
print("=" * 60)

REQUIRED_DIRS = {
    "CheXpert":    CHEXPERT_DIR,
    "ChestX6":     CHESTX6_DIR,
    "COVID-QU-Ex": COVIDQU_DIR,
}

REQUIRED_FILES = {
    "CheXpert CSV":    os.path.join(CHEXPERT_DIR, "train.csv"),
    "CheXNet weights": CHEXNET_WEIGHTS,
}

all_present = True
for name, path in REQUIRED_DIRS.items():
    exists = os.path.exists(path)
    print(f"  {'OK' if exists else 'MISSING':<8} {name}: {path}")
    if not exists:
        all_present = False

for name, path in REQUIRED_FILES.items():
    exists = os.path.exists(path)
    print(f"  {'OK' if exists else 'MISSING':<8} {name}: {path}")
    if not exists:
        all_present = False

if not all_present:
    print("\nERROR: One or more required datasets are missing.")
    sys.exit(1)

print("\nAll datasets found. Starting...\n")

# ==============================================================================
# 3. CLASS DEFINITIONS — 8 clean classes, no NIH
# ==============================================================================
DISEASES = [
    "Normal", "Edema", "Pneumothorax",
    "Pneumonia-Bacterial", "Pneumonia-Viral", "COVID-19",
    "Tuberculosis", "Emphysema"
]

CHEXPERT_LABEL_MAP = {
    "No Finding":   "Normal",
    "Pneumothorax": "Pneumothorax",
    "Edema":        "Edema",
}

CHESTX6_LABEL_MAP = {
    "Pneumonia-Bacterial": "Pneumonia-Bacterial",
    "Pneumonia-Viral":     "Pneumonia-Viral",
    "Covid-19":            "COVID-19",
    "Tuberculosis":        "Tuberculosis",
    "Emphysema":           "Emphysema",
}

COVIDQU_LABEL_MAP = {
    "COVID-19": "COVID-19",
    "Normal":   "Normal",
}

CAP_PER_CLASS = 3000

# ==============================================================================
# 4. CUSTOM LAYER
# ==============================================================================
class DenseNetPreprocess(layers.Layer):
    """Applies DenseNet121 preprocessing inside the model.
    Using a proper Keras layer instead of Lambda avoids the safe_mode
    deserialization error when loading the model in Django on Windows.
    """
    def call(self, x):
        return tf.keras.applications.densenet.preprocess_input(x)

    def get_config(self):
        return super().get_config()

# ==============================================================================
# 5. DATASET LOADERS
# ==============================================================================
def load_chexpert_dataset() -> pd.DataFrame:
    print("\n--- Loading CheXpert ---")
    df = pd.read_csv(os.path.join(CHEXPERT_DIR, "train.csv"))
    label_cols = list(df.columns[5:])
    df[label_cols] = df[label_cols].fillna(0)

    # Frontal only
    df = df[df['Frontal/Lateral'] == 'Frontal'].copy()

    # Drop uncertain (-1)
    df = df[(df[label_cols] >= 0).all(axis=1)].copy()

    # Single-label only
    df = df[(df[label_cols] == 1).sum(axis=1) == 1].copy()

    df['raw_label'] = (df[label_cols] == 1).idxmax(axis=1)
    df['label'] = df['raw_label'].map(CHEXPERT_LABEL_MAP)
    df = df.dropna(subset=['label'])

    base = "/kaggle/input/datasets/willarevalo/chexpert-v10-small"
    df['filepath'] = df['Path'].apply(lambda p: os.path.join(base, p))
    df = df[df['filepath'].apply(os.path.exists)].copy()
    df['patient_id'] = "chex_" + df['Path'].str.extract(r'(patient\d+)')[0].fillna("unknown")

    print(f"CheXpert loaded: {len(df)} images")
    print(df['label'].value_counts())
    return df[['filepath', 'patient_id', 'label']]


def load_chestx6_dataset() -> pd.DataFrame:
    print("\n--- Loading ChestX6 ---")
    data = []
    for folder, label in CHESTX6_LABEL_MAP.items():
        found = 0
        for split in ['train', 'val', 'test', '']:
            folder_path = (
                os.path.join(CHESTX6_DIR, split, folder)
                if split else
                os.path.join(CHESTX6_DIR, folder)
            )
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                for img_path in glob.glob(os.path.join(folder_path, ext)):
                    data.append({
                        'filepath':   img_path,
                        'patient_id': f"chestx6_{os.path.basename(img_path)}",
                        'label':      label
                    })
                    found += 1
        print(f"  {label}: {found} images")

    df = pd.DataFrame(data)
    if df.empty:
        print("ERROR: ChestX6 no images found")
        return pd.DataFrame()

    df = df.drop_duplicates(subset=['filepath'])
    print(f"ChestX6 loaded: {len(df)} images")
    return df[['filepath', 'patient_id', 'label']]


def load_covidqu_dataset() -> pd.DataFrame:
    print("\n--- Loading COVID-QU-Ex ---")
    data = []
    for folder, label in COVIDQU_LABEL_MAP.items():
        found = 0
        for split in ['Train', 'Val', 'Test']:
            folder_path = os.path.join(COVIDQU_DIR, split, folder, "images")
            if not os.path.exists(folder_path):
                continue
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                for img_path in glob.glob(os.path.join(folder_path, ext)):
                    data.append({
                        'filepath':   img_path,
                        'patient_id': f"covidqu_{os.path.basename(img_path)}",
                        'label':      label
                    })
                    found += 1
        print(f"  {label}: {found} images")

    df = pd.DataFrame(data)
    if df.empty:
        print("ERROR: COVID-QU-Ex no images found")
        return pd.DataFrame()

    df = df.drop_duplicates(subset=['filepath'])
    print(f"COVID-QU-Ex loaded: {len(df)} images")
    return df[['filepath', 'patient_id', 'label']]


def build_master_dataframe() -> pd.DataFrame:
    chexpert = load_chexpert_dataset()
    chestx6  = load_chestx6_dataset()
    covidqu  = load_covidqu_dataset()

    master_df = pd.concat([chexpert, chestx6, covidqu], ignore_index=True)
    master_df = master_df.dropna(subset=['label', 'filepath'])
    master_df = master_df[master_df['filepath'].apply(os.path.exists)].copy()

    print(f"\nBefore capping: {len(master_df)} total images")
    print(master_df['label'].value_counts())

    print(f"\nCapping each class to {CAP_PER_CLASS}...")
    capped = []
    for label in DISEASES:
        subset = master_df[master_df['label'] == label]
        if len(subset) == 0:
            print(f"  WARNING  {label}: 0 images — class will be missing!")
            continue
        if len(subset) > CAP_PER_CLASS:
            subset = subset.sample(n=CAP_PER_CLASS, random_state=42)
            print(f"  CAPPED   {label}: {CAP_PER_CLASS}")
        else:
            print(f"  OK       {label}: {len(subset)}")
        capped.append(subset)

    master_df = pd.concat(capped, ignore_index=True)
    master_df = master_df.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"\nFinal: {len(master_df)} images across {master_df['label'].nunique()} classes")
    print(master_df['label'].value_counts())
    return master_df


# ==============================================================================
# 6. CLASS WEIGHTS
# ==============================================================================
def compute_class_weights(df: pd.DataFrame) -> dict:
    """Compute class weights to handle imbalance after capping."""
    label_to_idx = {d: i for i, d in enumerate(DISEASES)}
    counts = df['label'].value_counts()
    total = len(df)
    weights = {}
    print("\nClass weights:")
    for label in DISEASES:
        idx = label_to_idx[label]
        count = counts.get(label, 1)
        weight = total / (len(DISEASES) * count)
        weights[idx] = weight
        print(f"  {label:<22}: {weight:.3f} ({count} samples)")
    return weights


# ==============================================================================
# 7. PATIENT-LEVEL SPLIT
# ==============================================================================
def patient_level_split(df, val_size=0.10, test_size=0.10, random_state=42):
    ids = df['patient_id'].values

    gss = GroupShuffleSplit(1, test_size=test_size, random_state=random_state)
    train_val_idx, test_idx = next(gss.split(df, groups=ids))
    train_val_df = df.iloc[train_val_idx].reset_index(drop=True)
    test_df      = df.iloc[test_idx].reset_index(drop=True)

    val_frac = val_size / (1 - test_size)
    gss2 = GroupShuffleSplit(1, test_size=val_frac, random_state=random_state)
    train_idx, val_idx = next(gss2.split(train_val_df, groups=train_val_df['patient_id'].values))
    train_df = train_val_df.iloc[train_idx].reset_index(drop=True)
    val_df   = train_val_df.iloc[val_idx].reset_index(drop=True)

    assert not set(train_df.patient_id) & set(val_df.patient_id), "Train/val leak!"
    assert not set(train_df.patient_id) & set(test_df.patient_id), "Train/test leak!"

    print(f"\nTrain: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")
    return train_df, val_df, test_df


# ==============================================================================
# 8. TF.DATA PIPELINE
# ==============================================================================
AUTOTUNE     = tf.data.AUTOTUNE
IMAGE_SIZE   = (224, 224)
LABEL_TO_IDX = {d: i for i, d in enumerate(DISEASES)}


def df_to_dataset(df: pd.DataFrame, shuffle: bool = True, batch_size: int = 32) -> tf.data.Dataset:
    filepaths = df['filepath'].values
    labels    = np.array([LABEL_TO_IDX[l] for l in df['label']], dtype=np.int32)
    labels_oh = tf.keras.utils.to_categorical(labels, num_classes=len(DISEASES)).astype(np.float32)

    def load_and_preprocess(path, label):
        img = tf.io.read_file(path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, IMAGE_SIZE)
        img = tf.cast(img, tf.float32) / 255.0
        return img, label

    ds = tf.data.Dataset.from_tensor_slices((filepaths, labels_oh))
    if shuffle:
        ds = ds.shuffle(buffer_size=10000, reshuffle_each_iteration=True)
    ds = ds.map(load_and_preprocess, num_parallel_calls=AUTOTUNE)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(AUTOTUNE)
    return ds


# ==============================================================================
# 9. MODEL — ImageNet weights (CheXNet caused catastrophic forgetting in v9)
# ==============================================================================
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


def compile_model(model: tf.keras.Model, lr: float = 1e-4) -> tf.keras.Model:
    model.compile(
        optimizer=optimizers.Adam(learning_rate=lr),
        loss="categorical_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.AUC(name="auc"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ]
    )
    return model


# ==============================================================================
# 10. TRAINING
# ==============================================================================
if __name__ == "__main__":
    df = build_master_dataframe()
    class_weights = compute_class_weights(df)
    train_df, val_df, test_df = patient_level_split(df)

    train_ds = df_to_dataset(train_df, shuffle=True,  batch_size=32)
    val_ds   = df_to_dataset(val_df,   shuffle=False, batch_size=32)
    test_ds  = df_to_dataset(test_df,  shuffle=False, batch_size=32)

    model = compile_model(create_model(len(DISEASES)))
    model.summary()
    os.makedirs("/kaggle/working/saved_models", exist_ok=True)

    callbacks = [
        ModelCheckpoint(
            "/kaggle/working/saved_models/model_v10.keras",
            monitor="val_auc", save_best_only=True, mode="max", verbose=1
        ),
        EarlyStopping(
            monitor="val_auc", patience=5,
            restore_best_weights=True, mode="max"
        ),
        ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6, verbose=1
        ),
    ]

    print("\n--- Phase 1: Training Head (backbone frozen) ---")
    model.fit(
        train_ds, epochs=15, validation_data=val_ds,
        callbacks=callbacks, class_weight=class_weights
    )

    print("\n--- Phase 2: Fine-tuning top half of DenseNet ---")
    base_model = model.get_layer("densenet121")
    base_model.trainable = True
    for layer in base_model.layers[:len(base_model.layers) // 2]:
        layer.trainable = False

    model = compile_model(model, lr=1e-5)
    model.fit(
        train_ds, epochs=25, validation_data=val_ds,
        callbacks=callbacks, class_weight=class_weights
    )

    print("\n--- Final Evaluation ---")
    results = model.evaluate(test_ds)
    print(dict(zip(model.metrics_names, results)))

    from sklearn.metrics import classification_report
    preds        = model.predict(test_ds, verbose=1)
    pred_classes = np.argmax(preds, axis=1)
    true_classes = np.array([LABEL_TO_IDX[l] for l in test_df['label']])

    print("\nPer-class report:")
    print(classification_report(true_classes, pred_classes, target_names=DISEASES))
