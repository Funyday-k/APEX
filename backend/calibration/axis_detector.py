"""Detect plot axis geometry using plot area bounds and local edge refinement."""

from __future__ import annotations

import cv2
import numpy as np


def detect_axes(img, plot_area: dict, margin_px: int = 2) -> dict:
    """Return axis line geometry, thin axis band bboxes, and inner plot area."""
    x0 = int(plot_area["x0"])
    y0 = int(plot_area["y0"])
    x1 = int(plot_area["x1"])
    y1 = int(plot_area["y1"])
    h, w = img.shape[:2]

    x_axis_y, x_conf = _refine_horizontal_axis(img, x0, x1, y1, search_below=True)
    y_axis_x, y_conf = _refine_vertical_axis(img, y0, y1, x0, search_left=True)

    x_band_h = max(2, int((y1 - y0) * 0.008))
    y_band_w = max(2, int((x1 - x0) * 0.008))

    inner = plot_area_from_axes(
        {
            "x_axis": {"y_pixel": x_axis_y, "x_start": x0, "x_end": x1},
            "y_axis": {"x_pixel": y_axis_x, "y_start": y0, "y_end": y1},
        },
        w,
        h,
        margin_px=margin_px,
    )

    return {
        "x_axis": {
            "y_pixel": int(x_axis_y),
            "x_start": x0,
            "x_end": x1,
            "confidence": round(x_conf, 3),
        },
        "y_axis": {
            "x_pixel": int(y_axis_x),
            "y_start": y0,
            "y_end": y1,
            "confidence": round(y_conf, 3),
        },
        "x_axis_bbox": {
            "x0": x0,
            "y0": max(0, int(x_axis_y) - x_band_h),
            "x1": x1,
            "y1": min(h, int(x_axis_y) + x_band_h),
        },
        "y_axis_bbox": {
            "x0": max(0, int(y_axis_x) - y_band_w),
            "y0": y0,
            "x1": min(w, int(y_axis_x) + y_band_w),
            "y1": y1,
        },
        "inner_plot_area": inner,
    }


def plot_area_from_axes(
    axis_geometry: dict,
    img_w: int,
    img_h: int,
    margin_px: int = 2,
) -> dict:
    """Plot data region inside detected x/y axes (above x-axis, right of y-axis)."""
    x_axis = axis_geometry.get("x_axis") or {}
    y_axis = axis_geometry.get("y_axis") or {}
    y_line = int(x_axis.get("y_pixel", img_h * 0.9))
    x_line = int(y_axis.get("x_pixel", img_w * 0.1))
    x_start = int(x_axis.get("x_start", x_line))
    x_end = int(x_axis.get("x_end", img_w - 1))
    y_start = int(y_axis.get("y_start", 0))
    y_end = int(y_axis.get("y_end", y_line))

    x0 = min(img_w - 2, max(0, x_line + margin_px))
    y0 = min(img_h - 2, max(0, y_start + margin_px))
    x1 = min(img_w - 1, max(x0 + 1, x_end - margin_px))
    y1 = min(img_h - 1, max(y0 + 1, y_line - margin_px))

    if y1 <= y0 or x1 <= x0:
        x0, y0, x1, y1 = x_line + margin_px, y_start, x_end, y_line

    return {
        "x0": int(x0),
        "y0": int(y0),
        "x1": int(x1),
        "y1": int(y1),
        "detected": True,
    }


def _parabolic_peak_offset(profile: np.ndarray, peak_idx: int) -> float:
    """Sub-pixel peak offset via parabolic fit on three samples."""
    if peak_idx <= 0 or peak_idx >= len(profile) - 1:
        return 0.0
    y0, y1, y2 = float(profile[peak_idx - 1]), float(profile[peak_idx]), float(profile[peak_idx + 1])
    denom = y0 - 2 * y1 + y2
    if abs(denom) < 1e-6:
        return 0.0
    return 0.5 * (y0 - y2) / denom


def _refine_horizontal_axis(
    img,
    x_start: int,
    x_end: int,
    seed_y: int,
    search_below: bool = True,
) -> tuple[int, float]:
    """Find strongest horizontal edge near expected x-axis position."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape[:2]
    span = max(1, x_end - x_start)
    band = max(12, int(span * 0.05))
    y_lo = max(0, seed_y - band // 3)
    y_hi = min(h - 1, seed_y + band if search_below else seed_y + band // 3)

    roi = gray[y_lo : y_hi + 1, max(0, x_start) : min(w, x_end)]
    if roi.size == 0:
        return seed_y, 0.45

    sobel = cv2.Sobel(roi, cv2.CV_32F, 0, 1, ksize=3)
    row_strength = np.mean(np.abs(sobel), axis=1)
    if row_strength.size == 0:
        return seed_y, 0.45

    # Projection + Hough candidates fused
    peak_idx = int(np.argmax(row_strength))
    sub = _parabolic_peak_offset(row_strength, peak_idx)
    refined_y = y_lo + peak_idx + sub

    edges = cv2.Canny(roi, 40, 120)
    hough_y: list[float] = []
    min_len = max(20, int(span * 0.25))
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=40,
        minLineLength=min_len,
        maxLineGap=6,
    )
    if lines is not None:
        for line in lines:
            lx1, ly1, lx2, ly2 = line[0]
            angle = np.degrees(np.arctan2(abs(ly2 - ly1), abs(lx2 - lx1) + 1e-6))
            if angle < 8:
                hough_y.append((ly1 + ly2) / 2.0 + y_lo)

    if hough_y:
        refined_y = 0.55 * refined_y + 0.45 * float(np.median(hough_y))

    refined_y = int(round(refined_y))
    strength = float(row_strength[peak_idx])
    threshold = float(np.mean(row_strength) + 0.5 * np.std(row_strength))
    confidence = 0.5 + min(0.45, strength / (threshold + 1e-6) * 0.25)
    if abs(refined_y - seed_y) > band * 1.5:
        return seed_y, 0.4
    return refined_y, confidence


def _refine_vertical_axis(
    img,
    y_start: int,
    y_end: int,
    seed_x: int,
    search_left: bool = True,
) -> tuple[int, float]:
    """Find strongest vertical edge near expected y-axis position."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape[:2]
    span = max(1, y_end - y_start)
    band = max(12, int(span * 0.05))
    x_lo = max(0, seed_x - band if search_left else band // 3)
    x_hi = min(w - 1, seed_x + band // 3)

    roi = gray[max(0, y_start) : min(h, y_end), x_lo : x_hi + 1]
    if roi.size == 0:
        return seed_x, 0.45

    sobel = cv2.Sobel(roi, cv2.CV_32F, 1, 0, ksize=3)
    col_strength = np.mean(np.abs(sobel), axis=0)
    if col_strength.size == 0:
        return seed_x, 0.45

    peak_idx = int(np.argmax(col_strength))
    sub = _parabolic_peak_offset(col_strength, peak_idx)
    refined_x = x_lo + peak_idx + sub

    edges = cv2.Canny(roi, 40, 120)
    hough_x: list[float] = []
    min_len = max(20, int(span * 0.25))
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=40,
        minLineLength=min_len,
        maxLineGap=6,
    )
    if lines is not None:
        for line in lines:
            lx1, ly1, lx2, ly2 = line[0]
            angle = np.degrees(np.arctan2(abs(ly2 - ly1), abs(lx2 - lx1) + 1e-6))
            if angle > 82:
                hough_x.append((lx1 + lx2) / 2.0 + x_lo)

    if hough_x:
        refined_x = 0.55 * refined_x + 0.45 * float(np.median(hough_x))

    refined_x = int(round(refined_x))
    strength = float(col_strength[peak_idx])
    threshold = float(np.mean(col_strength) + 0.5 * np.std(col_strength))
    confidence = 0.5 + min(0.45, strength / (threshold + 1e-6) * 0.25)
    if abs(refined_x - seed_x) > band * 1.5:
        return seed_x, 0.4
    return refined_x, confidence
