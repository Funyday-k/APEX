import cv2
import numpy as np


def enhance(img: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(img, d=5, sigmaColor=30, sigmaSpace=30)


def upscale_if_small(img: np.ndarray, min_dim: int = 800) -> np.ndarray:
    h, w = img.shape[:2]
    scale = max(1.0, min_dim / min(h, w))
    if scale > 1.0:
        return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return img
