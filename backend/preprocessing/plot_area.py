import cv2
import numpy as np

from calibration.axis_detector import plot_area_from_axes


def _refine_right_edge(gray: np.ndarray, x0: int, y0: int, y1: int, x1_hint: int) -> int:
    """Extend plot right boundary using ink projection and vertical edges."""
    h, w = gray.shape[:2]
    y0 = max(0, min(y0, h - 1))
    y1 = max(y0 + 1, min(y1, h))
    band = gray[y0:y1, max(0, x0) : min(w, int(w * 0.98))]
    if band.size == 0:
        return x1_hint

    _, binary = cv2.threshold(band, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    col_sum = binary.sum(axis=0).astype(np.float32)
    if col_sum.max() <= 0:
        return x1_hint

    thresh = col_sum.max() * 0.08
    last_ink = x0
    for i, val in enumerate(col_sum):
        if val >= thresh:
            last_ink = x0 + i

    edges = cv2.Canny(gray, 40, 120)
    v_lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=60,
        minLineLength=int((y1 - y0) * 0.4),
        maxLineGap=8,
    )
    right_candidates = [x1_hint]
    if v_lines is not None:
        for line in v_lines:
            lx1, ly1, lx2, ly2 = line[0]
            angle = np.degrees(np.arctan2(abs(ly2 - ly1), abs(lx2 - lx1)))
            if angle > 75:
                vx = max(lx1, lx2)
                if x0 + (x1_hint - x0) * 0.5 < vx < w * 0.99:
                    right_candidates.append(int(vx))

    return int(min(w - 2, max(x1_hint, last_ink + 8, max(right_candidates))))


def constrain_plot_area_with_axes(
    plot_area: dict,
    axis_geometry: dict | None,
    img_w: int,
    img_h: int,
    margin_px: int = 2,
) -> dict:
    """Intersect Hough plot area with axis-inner rectangle when axes are confident."""
    if not axis_geometry:
        return plot_area
    inner = axis_geometry.get("inner_plot_area")
    if not inner and axis_geometry.get("x_axis") and axis_geometry.get("y_axis"):
        inner = plot_area_from_axes(axis_geometry, img_w, img_h, margin_px=margin_px)
    if not inner or not inner.get("detected"):
        return plot_area

    x_conf = float((axis_geometry.get("x_axis") or {}).get("confidence", 0))
    y_conf = float((axis_geometry.get("y_axis") or {}).get("confidence", 0))
    if min(x_conf, y_conf) < 0.45:
        return plot_area

    x0, y0, x1, y1 = intersect_rect(
        plot_area,
        inner["x0"],
        inner["y0"],
        inner["x1"],
        inner["y1"],
    )
    if x1 <= x0 or y1 <= y0:
        return plot_area
    return {
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
        "detected": plot_area.get("detected", True),
        "source": "axes_constrained",
    }


def detect_plot_area(img: np.ndarray, x_tick_pixels: list[int] | None = None) -> dict:
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

        right_v = [max(l[0], l[2]) for l in v_lines if max(l[0], l[2]) > x0 + 20]
        if right_v:
            x1 = max(x1, max(right_v))

        if x_tick_pixels:
            tick_right = max(x_tick_pixels) + 12
            x1 = max(x1, tick_right)

        x1 = _refine_right_edge(gray, x0, y0, y1, x1)

        return {
            "x0": int(x0),
            "y0": int(y0),
            "x1": int(x1),
            "y1": int(y1),
            "detected": True,
        }

    h, w = img.shape[:2]
    x1 = int(w * 0.95)
    if x_tick_pixels:
        x1 = max(x1, max(x_tick_pixels) + 12)
    return {
        "x0": int(w * 0.1),
        "y0": int(h * 0.1),
        "x1": min(w - 2, x1),
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
