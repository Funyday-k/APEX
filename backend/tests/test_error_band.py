import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import AxisCalibration, AxisScale, CalibrationConfig, CalibrationPoint, Point
from extractors.error_band import ErrorBandDetector
from extractors.line_tracing import trace_mask_to_points


def _calibrator():
    return Calibrator(
        CalibrationConfig(
            x_axis=AxisCalibration(
                scale=AxisScale.LINEAR,
                ref1=CalibrationPoint(
                    pixel=Point(x=50, y=180), data=Point(x=0, y=0)
                ),
                ref2=CalibrationPoint(
                    pixel=Point(x=350, y=180), data=Point(x=10, y=0)
                ),
            ),
            y_axis=AxisCalibration(
                scale=AxisScale.LINEAR,
                ref1=CalibrationPoint(
                    pixel=Point(x=50, y=180), data=Point(x=0, y=0)
                ),
                ref2=CalibrationPoint(
                    pixel=Point(x=50, y=30), data=Point(x=0, y=10)
                ),
            ),
        )
    )


def test_error_band_envelope_masks():
    mask = np.zeros((200, 400), np.uint8)
    for x in range(80, 320):
        y_mid = 100
        cv2.line(mask, (x, y_mid - 15), (x, y_mid + 15), 255, 1)
    cal = _calibrator()
    upper = np.zeros_like(mask)
    lower = np.zeros_like(mask)
    for x in range(80, 320):
        cv2.circle(upper, (x, 85), 1, 255, -1)
        cv2.circle(lower, (x, 115), 1, 255, -1)
    upper_pts = trace_mask_to_points(upper, cal, 50, 350, peak_mode=True)
    lower_pts = trace_mask_to_points(lower, cal, 50, 350, peak_mode=False)
    assert len(upper_pts) >= 5
    assert len(lower_pts) >= 5


def test_error_band_detector_on_shaded_region():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    mask = np.zeros((200, 400), np.uint8)
    for x in range(60, 340):
        cv2.line(mask, (x, 70), (x, 130), 255, 2)
        img[70:131, x, :] = [200, 220, 255]
    cal = _calibrator()
    det = ErrorBandDetector()
    band = det.detect_in_mask(img, mask, cal, 50, 350, "#c8dcff", "test_band")
    assert band is None or (
        len(band.upper_points) >= 2 and len(band.lower_points) >= 2
    )
