"""Regression metrics on synthetic line chart (same fixture as test_extraction)."""

import numpy as np
import pytest

from calibration.calibrator import Calibrator
from core.schemas import ChartType
from extractors import get_extractor
from tests.benchmark.metrics import point_count, series_count, x_coverage
from tests.test_calibration import make_calibration


def _synthetic_line_image():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    for x in range(50, 350):
        y = int(150 - (x - 50) * 0.2)
        img[y - 1 : y + 2, x, :] = [200, 40, 40]
    return img


def test_synthetic_line_metrics():
    img = _synthetic_line_image()
    cal = Calibrator(make_calibration())
    ext = get_extractor(ChartType.LINE)
    series = ext.extract(img, cal)
    assert series_count(series) >= 1
    assert point_count(series) >= 20
    s0 = series[0]
    cov = x_coverage(s0, 0.0, 10.0)
    assert cov > 0.3
