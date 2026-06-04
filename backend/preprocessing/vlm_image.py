"""Prepare normalized image bytes for VLM (EXIF-corrected, same as CV pipeline)."""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

from preprocessing.enhance import enhance
from preprocessing.loader import load_image


def prepare_vlm_image(image_bytes: bytes, apply_enhance: bool = True) -> tuple[bytes, np.ndarray, int, int]:
    """Return PNG bytes and RGB array with consistent orientation/size for VLM + CV."""
    img = load_image(image_bytes)
    if apply_enhance:
        img = enhance(img)
    h, w = img.shape[:2]
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue(), img, w, h
