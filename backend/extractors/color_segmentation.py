import cv2
import numpy as np
from sklearn.cluster import KMeans


def segment_by_color(
    img: np.ndarray,
    plot_mask: np.ndarray,
    n_colors: int | None = None,
    given_colors: list[str] | None = None,
) -> dict:
    if given_colors:
        return _segment_by_given_colors(img, plot_mask, given_colors)

    ys, xs = np.where(plot_mask > 0)
    pixels = img[ys, xs].astype(float)

    sat = _saturation(pixels)
    colored = pixels[sat > 30]
    if len(colored) < 50:
        return {"#000000": _black_line_mask(img, plot_mask)}

    k = n_colors or _estimate_color_count(colored)
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(colored)
    centers = km.cluster_centers_.astype(int)

    masks = {}
    for c in centers:
        hexc = "#%02x%02x%02x" % tuple(c)
        masks[hexc] = _color_mask(img, plot_mask, c, tol=35)
    return masks


def _saturation(rgb: np.ndarray) -> np.ndarray:
    mx = rgb.max(axis=1)
    mn = rgb.min(axis=1)
    return np.where(mx > 0, (mx - mn) / mx * 255, 0)


def _color_mask(img, plot_mask, color, tol=35):
    diff = np.linalg.norm(img.astype(float) - color, axis=2)
    return ((diff < tol) & (plot_mask > 0)).astype(np.uint8) * 255


def _black_line_mask(img, plot_mask):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return ((gray < 80) & (plot_mask > 0)).astype(np.uint8) * 255


def _estimate_color_count(colored: np.ndarray, max_k=6) -> int:
    best_k, prev_inertia = 1, None
    for k in range(1, max_k + 1):
        km = KMeans(n_clusters=k, n_init=5, random_state=0).fit(colored)
        if prev_inertia and prev_inertia - km.inertia_ < prev_inertia * 0.1:
            break
        prev_inertia, best_k = km.inertia_, k
    return best_k


def _segment_by_given_colors(img, plot_mask, hex_colors):
    masks = {}
    for hexc in hex_colors:
        c = np.array([int(hexc[i : i + 2], 16) for i in (1, 3, 5)])
        masks[hexc] = _color_mask(img, plot_mask, c, tol=40)
    return masks
