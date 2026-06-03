import numpy as np
import pytest

from calibration.calibrator import Calibrator
from core.schemas import (
    AxisCalibration,
    AxisScale,
    CalibrationConfig,
    CalibrationPoint,
    ChartType,
    Point,
)
from extractors import get_extractor
from tests.test_calibration import make_calibration


def _synthetic_line_image():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    for x in range(50, 350):
        y = int(150 - (x - 50) * 0.2)
        img[y - 1 : y + 2, x, :] = [200, 40, 40]
    return img


def test_line_extractor_returns_series():
    img = _synthetic_line_image()
    cal = Calibrator(make_calibration())
    ext = get_extractor(ChartType.LINE)
    series = ext.extract(img, cal)
    assert len(series) >= 1
    assert len(series[0].points) >= 2


def test_get_extractor_factory():
    assert get_extractor(ChartType.SCATTER) is not None
    assert get_extractor(ChartType.BAR) is not None
