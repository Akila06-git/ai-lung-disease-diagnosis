import os
import sys
from pathlib import Path

# Disable oneDNN if it's causing issues
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "0"

# Add the current directory to sys.path so we can import ml_model
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_load():
    try:
        import tensorflow as tf
        print("TensorFlow version:", tf.__version__)
        sys.stdout.flush()
        
        default_path = "ml_model/saved_models/model.keras"
        print(f"Checking if {default_path} exists: {os.path.exists(default_path)}")
        sys.stdout.flush()
        
        print("Starting model load (tf_keras.models.load_model)...")
        sys.stdout.flush()
        
        import tf_keras
        print("TF-Keras version:", tf_keras.__version__)
        sys.stdout.flush()
        
        model = tf_keras.models.load_model(default_path, compile=False)
        print("Model loaded successfully with TF-Keras!")
        sys.stdout.flush()
        print(model.summary())
        sys.stdout.flush()
    except Exception as e:
        print("Error loading model:", e)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    except BaseException as e:
        print("Caught BaseException:", e)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()


if __name__ == "__main__":
    test_load()

