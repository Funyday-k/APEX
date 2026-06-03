import cv2
import numpy as np


def detect_plot_area(img: np.ndarray) -> dict:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=100,
        minLineLength=min(img.shape[:2]) // 3,
        maxLineGap=10,
    )

    h_lines, v_lines = [], []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(abs(y2 - y1), abs(x2 - x1)))
            if angle < 5:
                h_lines.append((x1, y1, x2, y2))
            elif angle > 85:
                v_lines.append((x1, y1, x2, y2))

    if h_lines and v_lines:
        x_axis = max(h_lines, key=lambda l: l[1])
        y_axis = min(v_lines, key=lambda l: l[0])
        x0 = min(y_axis[0], y_axis[2])
        y1 = max(x_axis[1], x_axis[3])
        x1 = max(x_axis[0], x_axis[2])
        y0 = min(y_axis[1], y_axis[3])
        return {
            "x0": int(x0),
            "y0": int(y0),
            "x1": int(x1),
            "y1": int(y1),
            "detected": True,
        }

    h, w = img.shape[:2]
    return {
        "x0": int(w * 0.1),
        "y0": int(h * 0.1),
        "x1": int(w * 0.95),
        "y1": int(h * 0.9),
        "detected": False,
    }


def intersect_rect(a: dict, x0: int, y0: int, x1: int, y1: int) -> tuple[int, int, int, int]:
    """Intersect calibration rectangle with detected plot area dict."""
    if not a.get("detected"):
        return x0, y0, x1, y1
    return (
        max(x0, a["x0"]),
        max(y0, a["y0"]),
        min(x1, a["x1"]),
        min(y1, a["y1"]),
    )
