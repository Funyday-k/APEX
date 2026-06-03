import cv2
import numpy as np

from core.schemas import ChartType


def rule_based_hint(img: np.ndarray) -> ChartType | None:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    if _has_large_color_gradient(img):
        return ChartType.HEATMAP
    if _count_rectangles(gray) >= 3:
        return ChartType.BAR
    blob_count = _count_blobs(gray)
    if blob_count > 20:
        return ChartType.SCATTER
    if _has_continuous_curves(gray):
        return ChartType.LINE
    return None


def _has_large_color_gradient(img: np.ndarray) -> bool:
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1]
    return float(np.mean(sat > 80)) > 0.4


def _count_rectangles(gray: np.ndarray) -> int:
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    count = 0
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        if len(approx) == 4 and cv2.contourArea(c) > 500:
            count += 1
    return count


def _count_blobs(gray: np.ndarray) -> int:
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 10
    params.maxArea = 500
    detector = cv2.SimpleBlobDetector_create(params)
    return len(detector.detect(gray))


def _has_continuous_curves(gray: np.ndarray) -> bool:
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for c in contours:
        if cv2.arcLength(c, False) > gray.shape[1] * 0.5:
            return True
    return False
