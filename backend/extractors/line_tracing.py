"""Skeleton-based line tracing inside a binary mask."""

import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import Point


def morphological_skeleton(mask: np.ndarray) -> np.ndarray:
    """Zhang-Suen style thinning via morphological skeletonization."""
    img = (mask > 0).astype(np.uint8) * 255
    skel = np.zeros(img.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    temp = img.copy()
    while True:
        eroded = cv2.erode(temp, element)
        opened = cv2.dilate(eroded, element)
        subset = cv2.subtract(temp, opened)
        skel = cv2.bitwise_or(skel, subset)
        temp = eroded.copy()
        if cv2.countNonZero(temp) == 0:
            break
    return skel


def _connect_mask_gaps(mask: np.ndarray) -> np.ndarray:
    """Light morphological close to bridge small breaks in curve masks."""
    if cv2.countNonZero(mask) < 5:
        return mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return closed


def trace_mask_to_points(
    mask: np.ndarray,
    calibrator: Calibrator,
    x_min: int,
    x_max: int,
    *,
    peak_mode: bool = False,
) -> list[Point]:
    """
    Trace curves in mask using skeleton + column sampling within plot x range.
    peak_mode uses upper envelope (min y) for line chart peaks.
    """
    roi = _connect_mask_gaps(mask.copy())
    h, w = roi.shape
    x_min = max(0, x_min)
    x_max = min(w - 1, x_max)
    if x_max <= x_min:
        return []

    skel = morphological_skeleton(roi)
    work = skel if cv2.countNonZero(skel) >= 10 else roi

    points: list[Point] = []
    last_py: float | None = None
    for px in range(x_min, x_max + 1):
        ys = np.where(work[:, px] > 0)[0]
        if len(ys) == 0:
            if last_py is not None and points:
                points.append(calibrator.pixel_to_data(px, last_py))
            continue
        if peak_mode:
            py = float(np.min(ys))
        else:
            py = _robust_y(ys, prefer_upper=peak_mode)
        last_py = py
        points.append(calibrator.pixel_to_data(px, py))

    points = _interpolate_gaps(points, calibrator, x_min, x_max)
    return _smooth_by_x(points)


def _robust_y(ys: np.ndarray, prefer_upper: bool = False) -> float:
    if len(ys) <= 3:
        return float(np.min(ys) if prefer_upper else np.median(ys))
    gaps = np.where(np.diff(ys) > 3)[0]
    segments = np.split(ys, gaps + 1)
    if prefer_upper:
        return float(np.min([np.min(seg) for seg in segments if len(seg)]))
    largest = max(segments, key=len)
    return float(np.median(largest))


def _interpolate_gaps(
    points: list[Point], calibrator: Calibrator, x_min: int, x_max: int, max_gap: int = 4
) -> list[Point]:
    if len(points) < 2:
        return points
    pts = sorted(points, key=lambda p: p.x)
    out: list[Point] = [pts[0]]
    for i in range(1, len(pts)):
        prev = out[-1]
        cur = pts[i]
        px_prev = calibrator.data_to_pixel(prev.x, prev.y).x
        px_cur = calibrator.data_to_pixel(cur.x, cur.y).x
        gap = int(px_cur - px_prev)
        if 1 < gap <= max_gap:
            for g in range(1, gap):
                t = g / gap
                ix = px_prev + g
                iy = (1 - t) * calibrator.data_to_pixel(prev.x, prev.y).y + t * calibrator.data_to_pixel(
                    cur.x, cur.y
                ).y
                out.append(calibrator.pixel_to_data(ix, iy))
        out.append(cur)
    return out


def _smooth_by_x(points: list[Point], window: int = 5) -> list[Point]:
    if len(points) < window:
        return sorted(points, key=lambda p: p.x)
    pts = sorted(points, key=lambda p: p.x)
    ys = np.array([p.y for p in pts])
    half = window // 2
    ys_smooth = ys.copy()
    for i in range(len(ys)):
        lo = max(0, i - half)
        hi = min(len(ys), i + half + 1)
        ys_smooth[i] = np.median(ys[lo:hi])
    return [Point(x=pts[i].x, y=float(ys_smooth[i])) for i in range(len(pts))]
