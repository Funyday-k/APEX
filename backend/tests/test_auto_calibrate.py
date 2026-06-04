"""Tests for automatic calibration from ticks."""

from calibration.auto_calibrate import ticks_to_calibration_config


def test_ticks_to_calibration_linear():
    ticks = {
        "x_ticks": [
            {"pixel": 100, "value": 0.0},
            {"pixel": 300, "value": 0.05},
            {"pixel": 200, "value": 0.025},
        ],
        "y_ticks": [
            {"pixel": 50, "value": 1.0},
            {"pixel": 150, "value": 0.1},
        ],
    }
    axes = {
        "x_axis": {"y_pixel": 180, "x_start": 50, "x_end": 350},
        "y_axis": {"x_pixel": 40, "y_start": 30, "y_end": 170},
    }
    cfg = ticks_to_calibration_config(ticks, axes, "linear", "linear")
    assert cfg is not None
    assert cfg["x_axis"]["ref1"]["data"]["x"] == 0.0
    assert cfg["x_axis"]["ref2"]["data"]["x"] == 0.05
    assert cfg["y_axis"]["ref1"]["data"]["y"] == 1.0
    assert cfg["y_axis"]["ref2"]["data"]["y"] == 0.1


def test_ticks_to_calibration_log_rejects_nonpositive():
    ticks = {
        "x_ticks": [{"pixel": 100, "value": -1}, {"pixel": 200, "value": 1}],
        "y_ticks": [{"pixel": 50, "value": 1}, {"pixel": 150, "value": 10}],
    }
    axes = {
        "x_axis": {"y_pixel": 180},
        "y_axis": {"x_pixel": 40},
    }
    assert ticks_to_calibration_config(ticks, axes, "log", "linear") is None
