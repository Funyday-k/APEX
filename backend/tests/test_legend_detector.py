"""Tests for legend region detection."""

import cv2
import numpy as np

from preprocessing.legend_detector import detect_legend_regions


def test_detect_legend_in_upper_right():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    plot = {"x0": 50, "y0": 30, "x1": 350, "y1": 170, "detected": True}
    # Legend markers + text area
    cv2.circle(img, (300, 50), 5, (30, 120, 220), -1)
    cv2.circle(img, (300, 70), 5, (220, 80, 30), -1)
    cv2.putText(img, "Series A", (312, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.putText(img, "Series B", (312, 74), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    ocr = [
        {"text": "Series A", "center": (330, 50), "bbox": {"x0": 312, "y0": 42, "x1": 370, "y1": 56}},
        {"text": "Series B", "center": (330, 70), "bbox": {"x0": 312, "y0": 62, "x1": 370, "y1": 76}},
    ]
    regions = detect_legend_regions(img, plot, ocr, 400, 200)
    assert len(regions) >= 1
    assert regions[0].kind == "legend"


def test_detect_legend_lower_left():
    img = np.ones((220, 420, 3), dtype=np.uint8) * 255
    plot = {"x0": 60, "y0": 30, "x1": 380, "y1": 190, "detected": True}
    cv2.circle(img, (95, 175), 5, (30, 120, 220), -1)
    cv2.circle(img, (95, 195), 5, (220, 80, 30), -1)
    cv2.putText(img, "A", (108, 179), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.putText(img, "B", (108, 199), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    ocr = [
        {"text": "A", "center": (115, 175), "bbox": {"x0": 108, "y0": 168, "x1": 130, "y1": 182}},
        {"text": "B", "center": (115, 195), "bbox": {"x0": 108, "y0": 188, "x1": 130, "y1": 202}},
    ]
    regions = detect_legend_regions(img, plot, ocr, 420, 220)
    assert len(regions) >= 1
