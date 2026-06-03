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
    if len(xs) < 50:
        return {}

    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(float)
    pixels = lab[ys, xs]

    sat = _saturation_rgb(img[ys, xs])
    colored_idx = sat > 25
    colored = pixels[colored_idx]
    if len(colored) < 50:
        return {"#000000": _dark_line_mask(img, plot_mask)}

    k = n_colors or _estimate_color_count(colored)
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(colored)
    centers = km.cluster_centers_

    masks = {}
    for c in centers:
        hexc = _lab_to_hex(c)
        masks[hexc] = _color_mask_lab(img, plot_mask, c, tol=28)
    return masks


def _saturation_rgb(rgb: np.ndarray) -> np.ndarray:
    mx = rgb.max(axis=1)
    mn = rgb.min(axis=1)
    return np.where(mx > 0, (mx - mn) / mx * 255, 0)


def _lab_to_hex(lab_center: np.ndarray) -> str:
    patch = np.array([[lab_center]], dtype=np.uint8)
    rgb = cv2.cvtColor(patch, cv2.COLOR_LAB2RGB)[0, 0]
    return "#%02x%02x%02x" % tuple(int(x) for x in rgb)


def _color_mask_lab(img: np.ndarray, plot_mask: np.ndarray, lab_center, tol: float = 28):
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(float)
    diff = np.linalg.norm(lab - lab_center, axis=2)
    return ((diff < tol) & (plot_mask > 0)).astype(np.uint8) * 255


def _dark_line_mask(img, plot_mask):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1]
    dark = (gray < 90) & (plot_mask > 0) & (sat < 40)
    return dark.astype(np.uint8) * 255


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
    lab_img = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(float)
    for hexc in hex_colors:
        c_rgb = np.array([int(hexc[i : i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8)
        patch = np.array([[c_rgb]])
        c_lab = cv2.cvtColor(patch, cv2.COLOR_RGB2LAB)[0, 0].astype(float)
        diff = np.linalg.norm(lab_img - c_lab, axis=2)
        masks[hexc] = ((diff < 32) & (plot_mask > 0)).astype(np.uint8) * 255
    return masks
