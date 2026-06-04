import numpy as np

from calibration.tick_detector import build_tick_label_regions


def test_build_tick_label_regions_from_ocr():
    axes = {
        "x_axis": {"y_pixel": 170, "x_start": 50, "x_end": 350},
        "y_axis": {"x_pixel": 45, "y_start": 30, "y_end": 170},
    }
    ocr = [
        {
            "text": "0.0",
            "center": (80, 185),
            "bbox": {"x0": 70, "y0": 175, "x1": 90, "y1": 195},
            "confidence": 0.9,
        },
        {
            "text": "1.0",
            "center": (200, 185),
            "bbox": {"x0": 190, "y0": 175, "x1": 210, "y1": 195},
            "confidence": 0.9,
        },
        {
            "text": "0.5",
            "center": (30, 100),
            "bbox": {"x0": 15, "y0": 90, "x1": 42, "y1": 110},
            "confidence": 0.9,
        },
        {
            "text": "1.5",
            "center": (30, 150),
            "bbox": {"x0": 15, "y0": 140, "x1": 42, "y1": 160},
            "confidence": 0.9,
        },
    ]
    regions = build_tick_label_regions(ocr, axes, 400, 200)
    kinds = {r.kind for r in regions}
    assert "x_tick_labels" in kinds
    assert "y_tick_labels" in kinds
