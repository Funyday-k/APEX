"""Tests for plot area right-edge refinement."""

import numpy as np

from preprocessing.plot_area import _refine_right_edge, detect_plot_area


def test_detect_plot_area_fallback_has_wide_right():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    # Draw simple L-shaped axes
    img[180, 50:350] = 0
    img[50:180, 50] = 0
    area = detect_plot_area(img)
    assert area["x1"] >= int(400 * 0.5)


def test_refine_right_edge_extends():
    gray = np.ones((100, 200), dtype=np.uint8) * 255
    gray[40:90, 30:160] = 0
    x1 = _refine_right_edge(gray, 20, 30, 95, 120)
    assert x1 >= 120


def test_detect_with_tick_pixels():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    img[180, 50:380] = 0
    img[50:180, 50] = 0
    area = detect_plot_area(img, x_tick_pixels=[80, 160, 240, 320])
    assert area["x1"] >= 320
