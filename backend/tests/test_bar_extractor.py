import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import AxisCalibration, AxisScale, CalibrationConfig, CalibrationPoint, Point
from extractors.bar_chart import BarChartExtractor


def _calibrator():
    return Calibrator(
        CalibrationConfig(
            x_axis=AxisCalibration(
                scale=AxisScale.LINEAR,
                ref1=CalibrationPoint(
                    pixel=Point(x=60, y=350), data=Point(x=0, y=0)
                ),
                ref2=CalibrationPoint(
                    pixel=Point(x=540, y=350), data=Point(x=5, y=0)
                ),
            ),
            y_axis=AxisCalibration(
                scale=AxisScale.LINEAR,
                ref1=CalibrationPoint(
                    pixel=Point(x=60, y=350), data=Point(x=0, y=0)
                ),
                ref2=CalibrationPoint(
                    pixel=Point(x=60, y=50), data=Point(x=0, y=10)
                ),
            ),
        )
    )


def test_bar_extractor_finds_vertical_bars():
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    for i, cx in enumerate([120, 220, 320, 420]):
        h = 80 + i * 25
        cv2.rectangle(img, (cx - 25, 350 - h), (cx + 25, 350), (40, 100, 180), -1)
    ext = BarChartExtractor()
    series = ext.extract(img, _calibrator())
    assert len(series) >= 1
    assert len(series[0].points) >= 2
