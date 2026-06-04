"""Tests for error bar detection."""

import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import AxisCalibration, CalibrationConfig, CalibrationPoint, Point
from extractors.error_bar import ErrorBarDetector


def _calibrator():
    cfg = CalibrationConfig(
        x_axis=AxisCalibration(
            scale="linear",
            ref1=CalibrationPoint(pixel=Point(x=50, y=180), data=Point(x=0, y=0)),
            ref2=CalibrationPoint(pixel=Point(x=350, y=180), data=Point(x=1, y=0)),
        ),
        y_axis=AxisCalibration(
            scale="linear",
            ref1=CalibrationPoint(pixel=Point(x=50, y=180), data=Point(x=0, y=0)),
            ref2=CalibrationPoint(pixel=Point(x=50, y=30), data=Point(x=0, y=1)),
        ),
    )
    return Calibrator(cfg)


def test_vertical_error_bar():
    mask = np.zeros((200, 400), np.uint8)
    cx, cy = 200, 100
    cv2.line(mask, (cx, cy - 30), (cx, cy + 30), 255, 2)
    cv2.line(mask, (cx - 5, cy - 30), (cx + 5, cy - 30), 255, 2)
    cv2.line(mask, (cx - 5, cy + 30), (cx + 5, cy + 30), 255, 2)
    cv2.circle(mask, (cx, cy), 4, 255, -1)
    det = ErrorBarDetector()
    out = det.detect(mask, [(cx, cy)], _calibrator(), direction="vertical")
    assert len(out) == 1
    assert out[0].error is not None
    assert out[0].error.y_err_upper is not None or out[0].error.y_err_lower is not None
