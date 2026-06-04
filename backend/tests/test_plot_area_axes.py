"""Tests for axis-constrained plot area."""

from calibration.axis_detector import plot_area_from_axes
from preprocessing.plot_area import constrain_plot_area_with_axes


def test_plot_area_from_axes_inner_rectangle():
    axes = {
        "x_axis": {"y_pixel": 180, "x_start": 50, "x_end": 280, "confidence": 0.8},
        "y_axis": {"x_pixel": 45, "y_start": 25, "y_end": 175, "confidence": 0.8},
    }
    inner = plot_area_from_axes(axes, 400, 220, margin_px=3)
    assert inner["x0"] > 45
    assert inner["y1"] < 180
    assert inner["x1"] > inner["x0"]
    assert inner["y1"] > inner["y0"]


def test_constrain_plot_area_intersects():
    plot = {"x0": 10, "y0": 10, "x1": 300, "y1": 200, "detected": True}
    axes = {
        "x_axis": {"y_pixel": 180, "x_start": 50, "x_end": 280, "confidence": 0.8},
        "y_axis": {"x_pixel": 45, "y_start": 25, "y_end": 175, "confidence": 0.8},
    }
    inner = plot_area_from_axes(axes, 400, 220)
    axes["inner_plot_area"] = inner
    out = constrain_plot_area_with_axes(plot, axes, 400, 220)
    assert out["x0"] >= inner["x0"]
    assert out["y1"] <= inner["y1"]
    assert out["x1"] <= plot["x1"]
