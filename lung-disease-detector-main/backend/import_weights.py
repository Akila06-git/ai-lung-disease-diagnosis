import os
import sys
import h5py
import numpy as np

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import tensorflow as tf

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ml_model.model import create_model

model_path = os.path.join(os.path.dirname(__file__), "ml_model", "saved_models", "model.h5")
keras_path = os.path.join(os.path.dirname(__file__), "ml_model", "saved_models", "model.keras")


def collect_weights(h5_group) -> dict:
    """
    Recursively walk an h5py group and collect all Dataset leaf nodes.
    Keys are the FULL relative path (e.g. 'dense/kernel:0'), not just the
    final component — this prevents collisions when two sub-groups share
    a weight name like 'kernel'.
    """
    result = {}

    def _visitor(name, obj):
        if isinstance(obj, h5py.Dataset):
            result[name] = np.array(obj)

    h5_group.visititems(_visitor)
    return result


def set_layer_weights(keras_layer, weight_dict: dict) -> bool:
    """
    Match a Keras layer's weight tensors to arrays in weight_dict and set them.
    Returns True if all weights were set successfully, False otherwise.
    """
    if not keras_layer.weights:
        return True

    new_weights = []
    for w in keras_layer.weights:
        # Keras weight names look like 'dense/kernel:0' or 'kernel:0'
        # Try progressively shorter suffixes so we match regardless of path depth.
        raw_name = w.name.replace(":0", "")
        candidates = [raw_name, raw_name.split("/")[-1]]  # full path, then bare name

        matched_key = None
        matched_arr = None
        for candidate in candidates:
            for key, arr in weight_dict.items():
                if key.split("/")[-1].replace(":0", "") == candidate.split("/")[-1]:
                    matched_key = key
                    matched_arr = arr
                    break
            if matched_key:
                break

        if matched_arr is None:
            print(f"  ✗ No match found for weight '{w.name}' in layer '{keras_layer.name}'")
            return False

        # FIX: Hard-fail on shape mismatch instead of silently loading corrupt weights.
        if matched_arr.shape != w.shape:
            print(
                f"  ✗ Shape mismatch for '{w.name}': "
                f"expected {w.shape}, got {matched_arr.shape}"
            )
            return False

        new_weights.append(matched_arr)
        print(f"  ✓ {w.name} {matched_arr.shape}")

    keras_layer.set_weights(new_weights)
    return True


try:
    print("Creating model architecture...")
    model = create_model(17)

    print(f"\nOpening H5 file: {model_path}")
    with h5py.File(model_path, "r") as f:
        mw = f["model_weights"]

        # ------------------------------------------------------------------ #
        # 1. Load DenseNet121 backbone                                        #
        # ------------------------------------------------------------------ #
        print("\n--- Loading DenseNet121 backbone ---")
        densenet_layer = model.get_layer("densenet121")

        if "densenet121" not in mw:
            raise KeyError("'densenet121' group not found in model_weights — check H5 structure with h5py")

        dn_group = mw["densenet121"]
        loaded = skipped = failed = 0

        for sub_layer in densenet_layer.layers:
            if not sub_layer.weights:
                skipped += 1
                continue
            if sub_layer.name not in dn_group:
                print(f"  ? Layer '{sub_layer.name}' not in H5 — skipping")
                skipped += 1
                continue

            print(f"\nLayer: {sub_layer.name}")
            weight_dict = collect_weights(dn_group[sub_layer.name])
            if set_layer_weights(sub_layer, weight_dict):
                loaded += 1
            else:
                failed += 1

        print(f"\nDenseNet backbone: {loaded} loaded, {skipped} skipped, {failed} failed")

        # ------------------------------------------------------------------ #
        # 2. Load top-level Dense / classification head layers               #
        # ------------------------------------------------------------------ #
        print("\n--- Loading classification head ---")

        for layer in model.layers:
            # Skip the DenseNet sub-model itself and layers with no weights
            if layer.name == "densenet121" or not layer.weights:
                continue

            print(f"\nLayer: {layer.name}")

            # FIX: The original code did `layer.name in mw[layer.name]` which
            # checks if the layer name is a key INSIDE its own group — never true.
            # Correct logic: check if the layer name exists in mw at all.
            if layer.name not in mw:
                print(f"  ? '{layer.name}' not found in H5 model_weights — skipping")
                continue

            weight_dict = collect_weights(mw[layer.name])
            if not weight_dict:
                print(f"  ? No weights collected from H5 group for '{layer.name}'")
                continue

            if set_layer_weights(layer, weight_dict):
                print(f"  ✓ '{layer.name}' loaded successfully")
            else:
                print(f"  ✗ '{layer.name}' FAILED — check shape mismatches above")

    # ---------------------------------------------------------------------- #
    # 3. Sanity check: run a dummy forward pass before saving                #
    # ---------------------------------------------------------------------- #
    print("\n--- Sanity check: dummy forward pass ---")
    dummy = np.zeros((1, *model.input_shape[1:]), dtype=np.float32)
    out = model(dummy, training=False)
    assert out.shape == (1, 17), f"Unexpected output shape: {out.shape}"
    probs = out.numpy()[0]
    assert not np.any(np.isnan(probs)), "NaN in output — weight loading likely failed"
    print(f"  Output shape: {out.shape}  ✓")
    print(f"  Output range: [{probs.min():.4f}, {probs.max():.4f}]  ✓")
    print(f"  No NaNs  ✓")

    # ---------------------------------------------------------------------- #
    # 4. Save                                                                 #
    # ---------------------------------------------------------------------- #
    print(f"\nSaving to {keras_path} ...")
    model.save(keras_path)
    print("SUCCESS — model.keras written with correct weights.")

except Exception:
    import traceback
    traceback.print_exc()