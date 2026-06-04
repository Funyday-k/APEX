"""Tests for hybrid marker line extraction."""

import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import AxisCalibration, CalibrationConfig, CalibrationPoint, Point
from extractors.line_chart import LineChartExtractor
from extractors.markers import detect_markers, is_marker_dominant


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


def test_marker_dominant_discrete_line():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    mask = np.zeros((200, 400), np.uint8)
    xs = [80, 140, 200, 260, 320]
    for x in xs:
        cv2.circle(img, (x, 120), 6, (200, 40, 40), -1)
        cv2.circle(mask, (x, 120), 6, 255, -1)
        if x > xs[0]:
            cv2.line(img, (xs[0], 120), (x, 120), (200, 40, 40), 2)
            cv2.line(mask, (xs[0], 120), (x, 120), 255, 2)
    centers = detect_markers(mask)
    assert len(centers) >= 3
    assert is_marker_dominant(mask, centers)


def test_line_extractor_uses_markers_not_dense_trace():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    xs = [80, 140, 200, 260, 320]
    for x in xs:
        cv2.circle(img, (x, 120), 7, (30, 120, 220), -1)
        if x > xs[0]:
            cv2.line(img, (xs[0], 120), (x, 120), (30, 120, 220), 2)
    ext = LineChartExtractor()
    series = ext.extract(img, _calibrator(), regions=None)
    assert len(series) >= 1
    pts = series[0].points
    assert len(pts) <= 12
    assert series[0].representation == "marker_line"
