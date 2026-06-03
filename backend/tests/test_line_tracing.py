import numpy as np

from calibration.calibrator import Calibrator
from extractors.line_tracing import morphological_skeleton, trace_mask_to_points
from tests.test_calibration import make_calibration


def test_skeleton_thins_line():
    mask = np.zeros((100, 200), np.uint8)
    mask[50, 20:180] = 255
    skel = morphological_skeleton(mask)
    assert cv2_count(skel) > 0


def cv2_count(m):
    return int((m > 0).sum())


def test_trace_returns_sorted_points():
    mask = np.zeros((200, 400), np.uint8)
    for x in range(50, 350):
        y = int(150 - (x - 50) * 0.15)
        mask[max(0, y - 1) : y + 2, x] = 255
    cal = Calibrator(make_calibration())
    pts = trace_mask_to_points(mask, cal, 50, 350)
    assert len(pts) >= 10
    xs = [p.x for p in pts]
    assert xs == sorted(xs)


try:
    import cv2  # noqa: F401
except ImportError:
    pass
