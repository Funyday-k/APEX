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


def trace_mask_to_points(
    mask: np.ndarray,
    calibrator: Calibrator,
    x_min: int,
    x_max: int,
) -> list[Point]:
    """
    Trace curves in mask using skeleton + column sampling within plot x range.
    Falls back to column median if skeleton is sparse.
    """
    roi = mask.copy()
    h, w = roi.shape
    x_min = max(0, x_min)
    x_max = min(w - 1, x_max)
    if x_max <= x_min:
        return []

    skel = morphological_skeleton(roi)
    work = skel if cv2.countNonZero(skel) >= 10 else roi

    points: list[Point] = []
    for px in range(x_min, x_max + 1):
        ys = np.where(work[:, px] > 0)[0]
        if len(ys) == 0:
            continue
        py = _robust_y(ys)
        points.append(calibrator.pixel_to_data(px, py))

    return _smooth_by_x(points)


def _robust_y(ys: np.ndarray) -> float:
    if len(ys) <= 3:
        return float(np.median(ys))
    gaps = np.where(np.diff(ys) > 3)[0]
    segments = np.split(ys, gaps + 1)
    largest = max(segments, key=len)
    return float(np.median(largest))


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
