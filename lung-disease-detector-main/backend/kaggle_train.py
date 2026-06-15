import os
import shutil
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.utils.class_weight import compute_class_weight
from pathlib import Path

# --- CONFIGURATION ---
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
# Kaggle Input Paths (Adjust if your dataset names are slightly different)
# Kaggle Input Paths (Dynamic Discovery)
def find_dataset_dir(root_dir, target_name):
    """Recursively search for specific folder name."""
    for root, dirs, files in os.walk(root_dir):
        if target_name in dirs:
            return Path(root) / target_name
    return None

print("Searching for datasets...")
COVID_INPUT_DIR = find_dataset_dir("/kaggle/input", "COVID-19_Radiography_Dataset")
TB_INPUT_DIR = find_dataset_dir("/kaggle/input", "TB_Chest_Radiography_Database")

if not COVID_INPUT_DIR:
    print("ERROR: Could not find 'COVID-19_Radiography_Dataset'")
if not TB_INPUT_DIR:
    print("ERROR: Could not find 'TB_Chest_Radiography_Database'")
    
print(f"Found COVID Dataset at: {COVID_INPUT_DIR}")
print(f"Found TB Dataset at: {TB_INPUT_DIR}")

# Output Directory (Writable)
WORKING_DIR = Path("/kaggle/working")
COMBINED_DIR = WORKING_DIR / "dataset" / "combined"
SAVED_MODEL_PATH = WORKING_DIR / "model.h5"

CLASSES = ["COVID-19", "Tuberculosis", "Bacterial Pneumonia", "Viral Pneumonia", "Normal"]

# --- 1. MODEL DEFINITION (from model.py) ---
def get_data_augmentation():
    return tf.keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
        layers.RandomContrast(0.1),
    ], name="data_augmentation")

def create_model(num_classes):
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(*IMAGE_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    inputs = layers.Input(shape=(*IMAGE_SIZE, 3))
    x = get_data_augmentation()(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    return models.Model(inputs, outputs, name="lung_disease_mobilenetv2")

def compile_model(model, base_learning_rate=1e-4):
    optimizer = optimizers.Adam(learning_rate=base_learning_rate)
    model.compile(
        optimizer=optimizer,
        loss="categorical_crossentropy",
        metrics=["accuracy", tf.keras.metrics.Precision(name="precision"), tf.keras.metrics.Recall(name="recall")],
    )
    return model

# --- 2. DATA PREPARATION ---
def copy_images(src, dest):
    """Copy images from src to dest."""
    src = Path(src)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    
    # Handle implicit 'images' subdirectory if present
    if (src / "images").exists():
        src = src / "images"
        
    print(f"Copying from {src} to {dest}...")
    count = 0
    for ext in ["*.png", "*.jpg", "*.jpeg"]:
        for f in src.glob(ext):
            try:
                shutil.copy(f, dest)
                count += 1
            except Exception:
                pass
    print(f"  -> Copied {count} images.")

def prepare_dataset():
    if COMBINED_DIR.exists():
        print("Dataset already looks prepared in /kaggle/working. Skipping copy.")
        return

    print("Setting up dataset in /kaggle/working/dataset/combined/...")
    
    # 1. COVID-19
    copy_images(COVID_INPUT_DIR / "COVID", COMBINED_DIR / "COVID-19")
    
    # 2. Viral Pneumonia
    copy_images(COVID_INPUT_DIR / "Viral Pneumonia", COMBINED_DIR / "Viral Pneumonia")
    
    # 3. Bacterial Pneumonia (Lung_Opacity in this dataset)
    copy_images(COVID_INPUT_DIR / "Lung_Opacity", COMBINED_DIR / "Bacterial Pneumonia")
    
    # 4. Tuberculosis
    copy_images(TB_INPUT_DIR / "Tuberculosis", COMBINED_DIR / "Tuberculosis")
    
    # 5. Normal (Combine from both)
    copy_images(COVID_INPUT_DIR / "Normal", COMBINED_DIR / "Normal")
    copy_images(TB_INPUT_DIR / "Normal", COMBINED_DIR / "Normal")

# --- 3. TRAINING LOOP (from train.py) ---
def main():
    prepare_dataset()
    
    # Generators
    # NOTE: Do NOT use rescale=1./255 here! The model already has
    # tf.keras.applications.mobilenet_v2.preprocess_input() built into its
    # graph, which handles normalization (maps [0,255] -> [-1,1]).
    # Also, do NOT add augmentation here — the model has built-in
    # data_augmentation layers (RandomFlip, RandomRotation, etc.).
    train_datagen = ImageDataGenerator(
        validation_split=0.30,
    )
    test_datagen = ImageDataGenerator(validation_split=0.30)

    print(f"Loading data from {COMBINED_DIR}...")
    train_generator = train_datagen.flow_from_directory(
        COMBINED_DIR, target_size=IMAGE_SIZE, batch_size=BATCH_SIZE, class_mode="categorical", subset="training"
    )
    temp_generator = test_datagen.flow_from_directory(
        COMBINED_DIR, target_size=IMAGE_SIZE, batch_size=BATCH_SIZE, class_mode="categorical", subset="validation", shuffle=False
    )

    # Split temp into val/test
    n_temp = temp_generator.samples
    indices = np.arange(n_temp)
    # Note: In a real script we might want deterministic split, but shuffle is fine here
    np.random.shuffle(indices)
    split = n_temp // 2
    val_idx, test_idx = indices[:split], indices[split:]

    def _make_subset(gen, subset_idx):
        gen_subset = ImageDataGenerator().flow_from_directory(
            gen.directory, target_size=gen.target_size, batch_size=gen.batch_size, 
            class_mode=gen.class_mode, shuffle=False
        )
        # Manually filter
        gen_subset.filenames = [gen.filenames[i] for i in subset_idx]
        gen_subset.samples = len(gen_subset.filenames)
        gen_subset.classes = gen.classes[subset_idx]
        gen_subset._set_index_array()
        return gen_subset

    # Simplifying validation/test split for Kaggle to avoid complex generator hacking issues
    # Just use the temp_generator as validation for simplicity in this script 
    # OR rely on the previous logic if it works. 
    # Let's stick to standard validation to be safe and robust.
    val_generator = temp_generator 

    # Calculate Class Weights
    y_train = train_generator.classes
    class_labels = np.unique(y_train)
    weights = compute_class_weight(class_weight="balanced", classes=class_labels, y=y_train)
    class_weights = {int(cls): float(w) for cls, w in zip(class_labels, weights)}
    print("Class Weights:", class_weights)

    # Build Model
    model = create_model(num_classes=len(CLASSES))
    model = compile_model(model, base_learning_rate=1e-4)

    callbacks = [
        ModelCheckpoint(str(SAVED_MODEL_PATH), monitor="val_accuracy", save_best_only=True, mode="max", verbose=1),
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, verbose=1),
    ]

    print("Starting Phase 1 Training...")
    model.fit(train_generator, epochs=15, validation_data=val_generator, class_weight=class_weights, callbacks=callbacks)

    print("Starting Phase 2 Fine-tuning...")
    base_model = model.get_layer("mobilenetv2_1.00_224")
    base_model.trainable = True
    fine_tune_at = len(base_model.layers) // 2
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False
    
    model = compile_model(model, base_learning_rate=1e-5)
    model.fit(train_generator, epochs=20, validation_data=val_generator, class_weight=class_weights, callbacks=callbacks)
    
    print(f"Training Complete. Model saved to {SAVED_MODEL_PATH}")

if __name__ == "__main__":
    main()
