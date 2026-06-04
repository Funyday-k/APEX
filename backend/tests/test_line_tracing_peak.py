"""Line tracing peak / gap handling."""

import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import AxisCalibration, CalibrationConfig, CalibrationPoint, Point
from extractors.line_tracing import trace_mask_to_points


def _calibrator():
    cfg = CalibrationConfig(
        x_axis=AxisCalibration(
            scale="linear",
            ref1=CalibrationPoint(pixel=Point(x=0, y=0), data=Point(x=0, y=0)),
            ref2=CalibrationPoint(pixel=Point(x=100, y=0), data=Point(x=1, y=0)),
        ),
        y_axis=AxisCalibration(
            scale="linear",
            ref1=CalibrationPoint(pixel=Point(x=0, y=100), data=Point(x=0, y=0)),
            ref2=CalibrationPoint(pixel=Point(x=0, y=0), data=Point(x=0, y=1)),
        ),
    )
    return Calibrator(cfg)


def test_peak_mode_uses_upper_envelope():
    mask = np.zeros((120, 120), np.uint8)
    for x in range(20, 100):
        mask[40, x] = 255
        mask[41, x] = 255
    cal = _calibrator()
    pts = trace_mask_to_points(mask, cal, 20, 99, peak_mode=True)
    assert len(pts) > 50
