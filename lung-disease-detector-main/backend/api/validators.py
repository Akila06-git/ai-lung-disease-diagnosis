from __future__ import annotations

import logging
from typing import IO

from django.conf import settings
from django.core.exceptions import ValidationError

from PIL import Image


logger = logging.getLogger(__name__)


def validate_file_extension(filename: str) -> None:
    """Validate that the filename has an allowed image extension."""
    from pathlib import Path

    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file extension '{ext}'. "
            "Allowed types are: .jpg, .jpeg, .png"
        )


def validate_file_size(file_obj: IO[bytes]) -> None:
    """Validate that the uploaded file does not exceed the size limit."""
    size = getattr(file_obj, "size", None)
    if size is None:
        # Fallback: try to seek to end
        pos = file_obj.tell()
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(pos)

    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError("File size exceeds 10MB limit.")


def _validate_magic_bytes(file_bytes: bytes) -> None:
    """Validate magic bytes to ensure the content is actually JPEG or PNG.

    Python 3.13 removed the stdlib ``imghdr`` module, so we manually check the
    most common signatures:
      - JPEG: FF D8 FF
      - PNG:  89 50 4E 47 0D 0A 1A 0A
    """
    header = file_bytes[:8]

    is_jpeg = len(header) >= 3 and header[0:3] == b"\xFF\xD8\xFF"
    is_png = (
        len(header) >= 8
        and header[0:8] == b"\x89PNG\r\n\x1a\n"
    )

    if not (is_jpeg or is_png):
        raise ValidationError("Uploaded file is not a valid JPEG or PNG image.")


def validate_image_content(file_obj: IO[bytes]) -> None:
    """Validate that the file is a real image using Pillow and magic bytes."""
    # Read a small portion for magic bytes verification
    pos = file_obj.tell()
    header = file_obj.read(4096)
    file_obj.seek(pos)

    if not header:
        raise ValidationError("Empty file uploaded.")

    _validate_magic_bytes(header)

    # Use Pillow to ensure we can open and verify the image
    try:
        with Image.open(file_obj) as img:
            img.verify()  # type: ignore[no-untyped-call]
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to verify image content: %s", exc)
        raise ValidationError("Uploaded file is not a valid image.")
    finally:
        file_obj.seek(0)

    # Re-open to check dimensions (verify() leaves file in unusable state)
    with Image.open(file_obj) as img:
        width, height = img.size
        if width < settings.MIN_IMAGE_WIDTH or height < settings.MIN_IMAGE_HEIGHT:
            raise ValidationError(
                f"Image dimensions too small. Minimum is "
                f"{settings.MIN_IMAGE_WIDTH}x{settings.MIN_IMAGE_HEIGHT}px."
            )
        file_obj.seek(0)


def validate_xray_image(file_obj: IO[bytes], filename: str) -> None:
    """Run all validations required for a chest X-ray upload."""
    from pathlib import Path
    
    validate_file_extension(filename)
    validate_file_size(file_obj)
    
    # DICOM files have their own format; skip standard image validation
    ext = Path(filename).suffix.lower()
    if ext in (".dcm", ".dicom"):
        return
    
    validate_image_content(file_obj)

