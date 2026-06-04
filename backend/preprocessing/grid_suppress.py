"""Suppress grid lines and axis strokes inside the plot region."""

import cv2
import numpy as np


def suppress_grid_and_axes(
    img: np.ndarray,
    plot_mask: np.ndarray,
    min_line_length: int | None = None,
    axis_inset_px: int = 2,
) -> np.ndarray:
    """
    Return a copy of plot_mask with long horizontal/vertical grid lines removed.
    Preserves colored data ink near axes.
    """
    h, w = plot_mask.shape[:2]
    if min_line_length is None:
        min_line_length = max(30, min(h, w) // 6)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    edges = cv2.bitwise_and(edges, plot_mask)

    line_mask = np.zeros((h, w), np.uint8)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=70,
        minLineLength=min_line_length,
        maxLineGap=6,
    )
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.hypot(x2 - x1, y2 - y1)
            if length < min_line_length:
                continue
            angle = np.degrees(np.arctan2(abs(y2 - y1), abs(x2 - x1) + 1e-6))
            if angle < 6 or angle > 84:
                cv2.line(line_mask, (x1, y1), (x2, y2), 255, 1)

    cleaned = plot_mask.copy()
    cleaned[line_mask > 0] = 0

    low_sat = _low_saturation_mask(img, plot_mask, axis_inset_px=axis_inset_px)
    cleaned[low_sat > 0] = 0
    return cleaned


def _low_saturation_mask(
    img: np.ndarray, plot_mask: np.ndarray, axis_inset_px: int = 2
) -> np.ndarray:
    """Mask gray grid / axis pixels; skip narrow border band to keep axis-adjacent curves."""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    gray_stroke = (sat < 35) & (val < 215) & (plot_mask > 0)

    # Keep pixels with enough color saturation (curves)
    rgb = img.astype(np.int16)
    chroma = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    colored = chroma > 25
    gray_stroke = gray_stroke & ~colored

    if axis_inset_px > 0:
        core = np.zeros_like(plot_mask)
        ys, xs = np.where(plot_mask > 0)
        if len(xs):
            x0, x1 = xs.min() + axis_inset_px, xs.max() - axis_inset_px
            y0, y1 = ys.min() + axis_inset_px, ys.max() - axis_inset_px
            core[max(0, y0) : y1 + 1, max(0, x0) : x1 + 1] = 255
            gray_stroke = gray_stroke & (core > 0)

    return gray_stroke.astype(np.uint8) * 255


def foreground_data_mask(
    img: np.ndarray, plot_mask: np.ndarray, axis_inset_px: int = 2
) -> np.ndarray:
    """Plot region minus grid/axes; suitable for color segmentation input."""
    cleaned = suppress_grid_and_axes(img, plot_mask, axis_inset_px=axis_inset_px)
    return cleaned
