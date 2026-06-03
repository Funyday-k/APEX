import pytest

from calibration.calibrator import Calibrator
from core.schemas import (
    AxisCalibration,
    AxisScale,
    CalibrationConfig,
    CalibrationPoint,
    Point,
)


def make_calibration():
    return CalibrationConfig(
        x_axis=AxisCalibration(
            scale=AxisScale.LINEAR,
            ref1=CalibrationPoint(
                pixel=Point(x=100, y=500), data=Point(x=0, y=0)
            ),
            ref2=CalibrationPoint(
                pixel=Point(x=500, y=500), data=Point(x=10, y=0)
            ),
        ),
        y_axis=AxisCalibration(
            scale=AxisScale.LINEAR,
            ref1=CalibrationPoint(
                pixel=Point(x=100, y=500), data=Point(x=0, y=0)
            ),
            ref2=CalibrationPoint(
                pixel=Point(x=100, y=100), data=Point(x=0, y=100)
            ),
        ),
    )


def test_pixel_to_data():
    cal = Calibrator(make_calibration())
    pt = cal.pixel_to_data(300, 300)
    assert abs(pt.x - 5.0) < 1e-6
    assert abs(pt.y - 50.0) < 1e-6


def test_roundtrip():
    cal = Calibrator(make_calibration())
    pt = cal.pixel_to_data(250, 350)
    px = cal.data_to_pixel(pt.x, pt.y)
    assert abs(px.x - 250) < 1e-6
    assert abs(px.y - 350) < 1e-6
