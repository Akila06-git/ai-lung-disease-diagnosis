"""
Apply extracted NPZ weights to a freshly built model and save as .weights.h5.
"""
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
sys.path.insert(0, os.getcwd())

import numpy as np
import tensorflow as tf

from ml_model.model import create_model, compile_model

NUM_CLASSES = 5
NPZ_PATH = os.path.join("ml_model", "saved_models", "model_weights.npz")
OUTPUT_PATH = os.path.join("ml_model", "saved_models", "converted_model.weights.h5")

print("Building model...")
model = create_model(num_classes=NUM_CLASSES)
model = compile_model(model)

print(f"Loading extracted weights from {NPZ_PATH}...")
data = np.load(NPZ_PATH, allow_pickle=True)

# Build a mapping: h5_layer_path -> numpy array
# Keys in npz are like: "mobilenetv2_1.00_224__Conv1__kernel" (/ replaced with __)
h5_weights = {}
for key in data.files:
    original_path = key.replace("__", "/")
    h5_weights[original_path] = data[key]

print(f"Found {len(h5_weights)} weight arrays in NPZ")

# Now map to model layers
applied = 0
skipped = 0

for layer in model.layers:
    current_weights = layer.get_weights()
    if not current_weights:
        continue

    layer_name = layer.name

    # Check if this is the base model (has sub-layers)
    if hasattr(layer, 'layers') and len(layer.layers) > 0:
        # This is a nested model (e.g., mobilenetv2)
        print(f"\nProcessing nested model: {layer_name} ({len(layer.layers)} sub-layers)")
        for sublayer in layer.layers:
            sub_weights = sublayer.get_weights()
            if not sub_weights:
                continue

            sublayer_name = sublayer.name
            # Look for weights matching this sublayer
            matching = {}
            prefix = f"{layer_name}/{sublayer_name}/"
            for h5_key, h5_val in h5_weights.items():
                if h5_key.startswith(prefix):
                    weight_name = h5_key[len(prefix):]
                    matching[weight_name] = h5_val

            if matching:
                # Build weight list in the order the layer expects
                expected_names = [w.name.split("/")[-1].rstrip(":0") for w in sublayer.weights]
                try:
                    new_weights = []
                    for en in expected_names:
                        # Try exact match first
                        if en in matching:
                            new_weights.append(matching[en])
                        elif en.replace("_", ":") in matching:
                            new_weights.append(matching[en.replace("_", ":")])
                        else:
                            # Try fuzzy match
                            found = False
                            for mk, mv in matching.items():
                                if mk.replace(":", "_") == en or mk == en:
                                    new_weights.append(mv)
                                    found = True
                                    break
                            if not found:
                                raise KeyError(f"No match for weight '{en}' in {list(matching.keys())}")

                    sublayer.set_weights(new_weights)
                    applied += len(new_weights)
                except Exception as e:
                    print(f"  WARNING: Could not set weights for {layer_name}/{sublayer_name}: {e}")
                    skipped += len(sub_weights)
            else:
                skipped += len(sub_weights)
    else:
        # Simple layer (dense, dropout, etc.)
        matching = {}
        for h5_key, h5_val in h5_weights.items():
            if h5_key.startswith(f"{layer_name}/"):
                weight_name = h5_key.split("/")[-1]
                matching[weight_name] = h5_val

        if matching:
            expected_names = [w.name.split("/")[-1].rstrip(":0") for w in layer.weights]
            try:
                new_weights = []
                for en in expected_names:
                    if en in matching:
                        new_weights.append(matching[en])
                    else:
                        found = False
                        for mk, mv in matching.items():
                            if mk.replace(":", "_") == en:
                                new_weights.append(mv)
                                found = True
                                break
                        if not found:
                            raise KeyError(f"No match for weight '{en}' in {list(matching.keys())}")

                layer.set_weights(new_weights)
                applied += len(new_weights)
                print(f"  Set weights for {layer_name}: {[w.shape for w in new_weights]}")
            except Exception as e:
                print(f"  WARNING: Could not set weights for {layer_name}: {e}")
                skipped += len(current_weights)
        else:
            skipped += len(current_weights)

print(f"\nApplied {applied} weight arrays, skipped {skipped}")

# Save the model weights in Keras 3 format
print(f"Saving to {OUTPUT_PATH}...")
model.save_weights(OUTPUT_PATH)
print(f"Done! Weights saved to {OUTPUT_PATH}")

# Quick verification
print("\nVerification - running a test prediction...")
test_input = np.random.rand(1, 224, 224, 3).astype(np.float32)
preds = model.predict(test_input, verbose=0)
print(f"Test prediction output: {preds}")
print(f"Prediction shape: {preds.shape}")
print(f"Sum of predictions: {preds.sum():.4f} (should be ~1.0)")
