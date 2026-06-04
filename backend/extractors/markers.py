"""Shared marker/blob detection for scatter and hybrid line charts."""

from __future__ import annotations

import cv2
import numpy as np


def detect_markers(
    mask: np.ndarray,
    *,
    min_area: int = 8,
    max_area: int = 1200,
    max_dim: int = 40,
) -> list[tuple[float, float]]:
    """Detect discrete marker centroids in a binary color mask."""
    centers: list[tuple[float, float]] = []

    gray = mask.copy()
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = min_area
    params.maxArea = max_area
    params.filterByCircularity = False
    params.filterByConvexity = False
    params.filterByInertia = False
    detector = cv2.SimpleBlobDetector_create(params)
    kps = detector.detect(gray)
    if kps:
        centers.extend((float(k.pt[0]), float(k.pt[1])) for k in kps)

    # Connected components on eroded mask (separate markers linked by thin lines)
    eroded = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1)
    n, _, stats, centroids = cv2.connectedComponentsWithStats(eroded, connectivity=8)
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        w_ = stats[i, cv2.CC_STAT_WIDTH]
        h_ = stats[i, cv2.CC_STAT_HEIGHT]
        aspect = w_ / max(h_, 1)
        if min_area <= area <= max_area and 0.25 <= aspect <= 4.0 and h_ < max_dim and w_ < max_dim:
            cx, cy = centroids[i]
            centers.append((float(cx), float(cy)))

    # Distance-transform peaks (markers on thick/connected strokes)
    if cv2.countNonZero(mask) > 0:
        dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        peak_thresh = max(3.0, float(dist.max()) * 0.45)
        dilated = cv2.dilate(dist, np.ones((3, 3), np.uint8))
        peaks = (dist >= peak_thresh) & (dist >= dilated - 1e-3)
        n_p, _, stats_p, centroids_p = cv2.connectedComponentsWithStats(
            peaks.astype(np.uint8), connectivity=8
        )
        for i in range(1, n_p):
            area = stats_p[i, cv2.CC_STAT_AREA]
            if area <= 0:
                continue
            cx, cy = centroids_p[i]
            centers.append((float(cx), float(cy)))

    return _dedupe_centers(centers, merge_px=10)


def _dedupe_centers(centers: list[tuple[float, float]], merge_px: float = 10) -> list[tuple[float, float]]:
    if not centers:
        return []
    out: list[tuple[float, float]] = []
    for cx, cy in centers:
        if not any(abs(cx - ox) < merge_px and abs(cy - oy) < merge_px for ox, oy in out):
            out.append((cx, cy))
    return out


def mask_without_markers(mask: np.ndarray, centers: list[tuple], radius: int = 8) -> np.ndarray:
    out = mask.copy()
    for cx, cy in centers:
        cv2.circle(out, (int(cx), int(cy)), radius, 0, -1)
    return out


def is_marker_dominant(mask: np.ndarray, centers: list[tuple], min_markers: int = 3) -> bool:
    """True when blob markers are likely the primary data representation."""
    if len(centers) >= min_markers:
        return True
    if len(centers) >= 2:
        total = cv2.countNonZero(mask)
        if total < 80:
            return True
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        large = sum(
            1
            for i in range(1, n)
            if stats[i, cv2.CC_STAT_AREA] >= 20 and stats[i, cv2.CC_STAT_WIDTH] >= 4
        )
        if large >= 2 and total / max(len(centers), 1) < 200:
            return True
    # Fallback: many distance-transform peaks along x
    if len(centers) >= 2:
        xs = sorted(c[0] for c in centers)
        if len(xs) >= 2 and (xs[-1] - xs[0]) / max(len(xs) - 1, 1) > 15:
            return True
    return False
