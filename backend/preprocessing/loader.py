import io

import numpy as np
from PIL import Image


def load_image(image_bytes: bytes) -> np.ndarray:
    pil = Image.open(io.BytesIO(image_bytes))

    if pil.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", pil.size, (255, 255, 255))
        pil = pil.convert("RGBA")
        background.paste(pil, mask=pil.split()[-1])
        pil = background
    else:
        pil = pil.convert("RGB")

    pil = _apply_exif_orientation(pil)
    return np.array(pil)


def _apply_exif_orientation(pil: Image.Image) -> Image.Image:
    try:
        from PIL import ImageOps

        return ImageOps.exif_transpose(pil)
    except Exception:
        return pil
