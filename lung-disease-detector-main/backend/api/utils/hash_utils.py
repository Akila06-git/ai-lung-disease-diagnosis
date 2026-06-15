from __future__ import annotations

import hashlib
from typing import IO

import cv2
import numpy as np
from PIL import Image


def generate_image_hash(file_obj: IO[bytes]) -> str:
    """Generate a SHA-256 hash of the raw image bytes.

    The file pointer is reset to the beginning after hashing.
    """
    pos = file_obj.tell()
    file_obj.seek(0)
    sha = hashlib.sha256()
    for chunk in iter(lambda: file_obj.read(8192), b""):
        sha.update(chunk)
    file_obj.seek(pos)
    return sha.hexdigest()


def generate_perceptual_hash(file_obj: IO[bytes], size: int = 32) -> str:
    """Generate a simple perceptual hash for approximate duplicate detection.

    This implementation uses a DCT-based pHash-style algorithm without external
    dependencies to keep the environment minimal.
    """
    pos = file_obj.tell()
    file_obj.seek(0)
    with Image.open(file_obj) as img:
        img = img.convert("L").resize((size, size), Image.LANCZOS)
        pixels = np.asarray(img, dtype=np.float32)
    file_obj.seek(pos)

    # Discrete cosine transform (2D)
    dct = cv2.dct(pixels)
    dct_low_freq = dct[:8, :8]
    median_val = np.median(dct_low_freq)
    diff = dct_low_freq > median_val
    # Convert boolean matrix to hex string
    bits = "".join("1" if v else "0" for v in diff.flatten())
    return f"{int(bits, 2):0{len(bits) // 4}x}"

