"""Tests for CV linear/log scale detection."""

import numpy as np

from calibration.scale_detector import detect_axis_scale, infer_axis_scales


def test_linear_uniform_ticks():
    ticks = [
        {"pixel": 100.0, "value": 0.0},
        {"pixel": 200.0, "value": 0.5},
        {"pixel": 300.0, "value": 1.0},
    ]
    scale, conf = detect_axis_scale(ticks)
    assert scale == "linear"
    assert conf > 0.4


def test_log_decade_ticks():
    # Log-spaced values with linear pixel spacing should prefer log when values span decades
    pixels = np.linspace(50, 250, 5)
    values = 10 ** np.linspace(-2, 0, 5)
    ticks = [{"pixel": float(p), "value": float(v)} for p, v in zip(pixels, values)]
    scale, conf = detect_axis_scale(ticks)
    assert scale == "log"
    assert conf > 0.4


def test_linear_rejects_vlm_log_for_scientific_linear():
    pixels = np.linspace(80, 220, 4)
    values = [0.0, 0.25, 0.5, 1.0]
    ticks = {
        "x_ticks": [{"pixel": float(p), "value": v} for p, v in zip(pixels, values)],
        "y_ticks": [{"pixel": float(p), "value": v} for p, v in zip(pixels, values)],
    }
    out = infer_axis_scales(ticks, vlm_x_scale="log", vlm_y_scale="log")
    assert out["x_scale"] == "linear"
    assert out["y_scale"] == "linear"
