"""Suppress grid lines and axis strokes inside the plot region."""

import cv2
import numpy as np


def suppress_grid_and_axes(
    img: np.ndarray,
    plot_mask: np.ndarray,
    min_line_length: int | None = None,
) -> np.ndarray:
    """
    Return a copy of plot_mask with long horizontal/vertical lines removed
    (typical grid and axis strokes).
    """
    h, w = plot_mask.shape[:2]
    if min_line_length is None:
        min_line_length = max(20, min(h, w) // 8)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    edges = cv2.bitwise_and(edges, plot_mask)

    line_mask = np.zeros((h, w), np.uint8)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=60,
        minLineLength=min_line_length,
        maxLineGap=8,
    )
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(abs(y2 - y1), abs(x2 - x1) + 1e-6))
            if angle < 8 or angle > 82:
                cv2.line(line_mask, (x1, y1), (x2, y2), 255, 2)

    cleaned = plot_mask.copy()
    cleaned[line_mask > 0] = 0

    low_sat = _low_saturation_mask(img, plot_mask)
    cleaned[low_sat > 0] = 0
    return cleaned


def _low_saturation_mask(img: np.ndarray, plot_mask: np.ndarray) -> np.ndarray:
    """Mask gray grid / axis pixels (low saturation, not pure white background)."""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    gray_stroke = (sat < 40) & (val < 220) & (plot_mask > 0)
    return gray_stroke.astype(np.uint8) * 255


def foreground_data_mask(img: np.ndarray, plot_mask: np.ndarray) -> np.ndarray:
    """Plot region minus grid/axes; suitable for color segmentation input."""
    cleaned = suppress_grid_and_axes(img, plot_mask)
    return cleaned
