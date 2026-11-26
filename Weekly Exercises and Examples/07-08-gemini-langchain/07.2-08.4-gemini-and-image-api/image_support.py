"""Validate and strip image metadata in a separate, time-bounded process."""

import base64
import binascii
import json
import os
from pathlib import Path
import subprocess
import sys

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_BASE64_CHARS = 4 * ((MAX_IMAGE_BYTES + 2) // 3)


class ImageValidationError(Exception):
    def __init__(self, detail, status=400):
        self.detail = detail
        self.status = status
        super().__init__(detail)


def validate_image(image):
    try:
        raw = base64.b64decode(image.data, validate=True)
    except (ValueError, binascii.Error):
        raise ImageValidationError("The image upload is not valid. Choose it again.") from None
    if len(raw) > MAX_IMAGE_BYTES:
        raise ImageValidationError("Choose an image no larger than 5 MB.", 413)
    signature = b"\x89PNG\r\n\x1a\n" if image.mime_type == "image/png" else b"\xff\xd8\xff"
    if not raw.startswith(signature):
        raise ImageValidationError("The image contents do not match its format. Choose a JPG or PNG.")
    try:
        result = subprocess.run(
            [sys.executable, "-I", str(Path(__file__).with_name("image_worker.py")), image.mime_type],
            input=raw, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=8, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        header, pixels = result.stdout.split(b"\n", 1) if result.returncode == 0 else (b"{}", b"")
        metadata = json.loads(header)
        width, height = metadata.get("width"), metadata.get("height")
        if (type(width) is not int or type(height) is not int
                or width < 1 or height < 1 or width * height > 16_000_000
                or not pixels.startswith(signature) or len(pixels) > MAX_IMAGE_BYTES):
            raise ValueError("invalid worker result")
    except (subprocess.TimeoutExpired, OSError, ValueError, TypeError, AttributeError):
        raise ImageValidationError(
            "This image could not be read. Use a still JPG or PNG up to 5 MB and 16 megapixels."
        ) from None
    cleaned = image.model_copy(update={"data": base64.b64encode(pixels).decode("ascii")})
    return cleaned, width, height
