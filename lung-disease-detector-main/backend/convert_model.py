"""
Extract weights from the saved .h5 model using h5py (raw access),
then apply them to a freshly built model and save as .weights.h5.

This bypasses all Keras deserialization issues.
"""
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import h5py
import numpy as np
import json
import sys

MODEL_PATH = os.path.join("ml_model", "saved_models", "model.h5")
OUTPUT_PATH = os.path.join("ml_model", "saved_models", "model_weights.npz")

print(f"Opening {MODEL_PATH}...")
f = h5py.File(MODEL_PATH, "r")

# Find the weight root
if "model_weights" in f:
    root = f["model_weights"]
    print("Found 'model_weights' group")
else:
    root = f
    print("Using root as weight group")

# Enumerate ALL datasets in the file recursively
all_datasets = {}
def visitor(name, obj):
    if isinstance(obj, h5py.Dataset):
        all_datasets[name] = np.array(obj)

root.visititems(visitor)

print(f"\nFound {len(all_datasets)} weight datasets:")
for name, arr in sorted(all_datasets.items()):
    print(f"  {name}: shape={arr.shape}")

# Save all weights as numpy arrays
print(f"\nSaving to {OUTPUT_PATH}...")
np.savez(OUTPUT_PATH, **{k.replace("/", "__"): v for k, v in all_datasets.items()})
print("Done!")

# Also dump a summary
summary_path = os.path.join("ml_model", "saved_models", "weight_summary.json")
summary = {k: list(v.shape) for k, v in sorted(all_datasets.items())}
with open(summary_path, "w") as sf:
    json.dump(summary, sf, indent=2)
print(f"Summary saved to {summary_path}")

f.close()
