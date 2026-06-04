"""Tests for VLM image normalization (EXIF + enhance pipeline)."""

import io

import numpy as np
from PIL import Image

from preprocessing.loader import load_image
from preprocessing.vlm_image import prepare_vlm_image


def test_prepare_vlm_image_matches_load_pipeline():
    arr = np.zeros((120, 200, 3), dtype=np.uint8)
    arr[:, :, 0] = 200
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    raw = buf.getvalue()

    vlm_bytes, img, w, h = prepare_vlm_image(raw)
    direct = load_image(raw)

    assert w == direct.shape[1]
    assert h == direct.shape[0]
    assert img.shape == direct.shape
    assert vlm_bytes[:4] == b"\x89PNG"
