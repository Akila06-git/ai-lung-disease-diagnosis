"""
DICOM (.dcm) file utilities for the Lung Disease Detector.

Converts raw PACS/DICOM X-ray files into standard PNG images
that can be fed into the DenseNet121 prediction pipeline.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def is_dicom_file(filename: str) -> bool:
    """Check if a filename has a DICOM extension."""
    return Path(filename).suffix.lower() in (".dcm", ".dicom")


def extract_dicom_metadata(ds) -> dict:
    """Extract patient metadata from a DICOM dataset.

    Returns a dict with keys: patient_name, patient_age, patient_sex.
    Missing fields default to empty string / None.
    """
    meta = {
        "patient_name": "",
        "patient_age": None,
        "patient_sex": "",
    }

    try:
        if hasattr(ds, "PatientName") and ds.PatientName:
            meta["patient_name"] = str(ds.PatientName)
    except Exception:
        pass

    try:
        if hasattr(ds, "PatientAge") and ds.PatientAge:
            # DICOM age is a string like "045Y"
            age_str = str(ds.PatientAge).replace("Y", "").replace("y", "").strip()
            meta["patient_age"] = int(age_str) if age_str.isdigit() else None
    except Exception:
        pass

    try:
        if hasattr(ds, "PatientSex") and ds.PatientSex:
            sex_map = {"M": "M", "F": "F", "O": "O"}
            meta["patient_sex"] = sex_map.get(str(ds.PatientSex).upper(), "O")
    except Exception:
        pass

    return meta


def convert_dicom_to_image(file_obj) -> Tuple[io.BytesIO, dict]:
    """Convert a DICOM file object to a PNG image in memory.

    Args:
        file_obj: A file-like object containing DICOM data.

    Returns:
        A tuple of (png_bytes_io, metadata_dict).
        The BytesIO object contains the PNG image data, seeked to 0.
    """
    import pydicom

    # Read DICOM data
    file_obj.seek(0)
    ds = pydicom.dcmread(file_obj)

    # Extract pixel array
    pixel_array = ds.pixel_array.astype(np.float64)

    # Handle Photometric Interpretation (invert if MONOCHROME1)
    if hasattr(ds, "PhotometricInterpretation"):
        if ds.PhotometricInterpretation == "MONOCHROME1":
            pixel_array = pixel_array.max() - pixel_array

    # Normalize to 8-bit (0-255)
    if pixel_array.max() > 0:
        pixel_array = ((pixel_array - pixel_array.min()) /
                       (pixel_array.max() - pixel_array.min()) * 255.0)
    pixel_array = pixel_array.astype(np.uint8)

    # Convert to PIL Image (grayscale -> RGB for the model)
    if len(pixel_array.shape) == 2:
        img = Image.fromarray(pixel_array, mode="L").convert("RGB")
    else:
        img = Image.fromarray(pixel_array).convert("RGB")

    # Save as PNG to a BytesIO object
    png_buffer = io.BytesIO()
    img.save(png_buffer, format="PNG")
    png_buffer.seek(0)

    # Extract metadata
    metadata = extract_dicom_metadata(ds)

    logger.info(
        "DICOM converted to PNG: %dx%d, metadata=%s",
        img.width, img.height, metadata
    )

    return png_buffer, metadata
