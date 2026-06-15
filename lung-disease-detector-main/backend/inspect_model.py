import os
import sys
import tensorflow as tf
import numpy as np

def inspect_model(model_path):
    print(f"Inspecting model: {model_path}")
    if not os.path.exists(model_path):
        print("Error: Model file not found.")
        return

    try:
        # Load model metadata without full weight loading if possible, 
        # but for .keras we usually load the whole thing.
        model = tf.keras.models.load_model(model_path, compile=False)
        
        print("\n--- Model Summary ---")
        model.summary()
        
        print("\n--- Input Details ---")
        for i, layer in enumerate(model.inputs):
            print(f"Input {i}: shape={layer.shape}, dtype={layer.dtype}")
            
        print("\n--- Output Details ---")
        for i, layer in enumerate(model.outputs):
            print(f"Output {i}: shape={layer.shape}, dtype={layer.dtype}")
            
        # Check for specific layers (Lambda, preprocess_input)
        print("\n--- Layer Check ---")
        for layer in model.layers:
            if "lambda" in layer.name.lower():
                print(f"Found Lambda layer: {layer.name}")
            if "rescaling" in layer.name.lower():
                print(f"Found Rescaling layer: {layer.name}")
            if "normalization" in layer.name.lower():
                print(f"Found Normalization layer: {layer.name}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    path = "ml_model/saved_models/model.keras"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    inspect_model(path)
