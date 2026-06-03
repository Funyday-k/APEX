def detect_axes(img, plot_area: dict) -> dict:
    x0, y0 = plot_area["x0"], plot_area["y0"]
    x1, y1 = plot_area["x1"], plot_area["y1"]
    return {
        "x_axis": {"y_pixel": y1, "x_start": x0, "x_end": x1},
        "y_axis": {"x_pixel": x0, "y_start": y0, "y_end": y1},
    }
