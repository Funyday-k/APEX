import cv2
import numpy as np
def detect_ticks(img, axes: dict, ocr_results: list) -> dict:
    x_ticks = _detect_x_ticks(img, axes["x_axis"], ocr_results)
    y_ticks = _detect_y_ticks(img, axes["y_axis"], ocr_results)
    return {"x_ticks": x_ticks, "y_ticks": y_ticks}


def _detect_x_ticks(img, x_axis, ocr_results):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    y_axis_px = x_axis["y_pixel"]
    ticks = []

    band = gray[y_axis_px + 1 : y_axis_px + 12, x_axis["x_start"] : x_axis["x_end"]]
    if band.size == 0:
        return ticks
    col_darkness = np.mean(255 - band, axis=0)
    peaks = _find_peaks(col_darkness, min_distance=15)

    for p in peaks:
        px = x_axis["x_start"] + p
        value = _match_label(ocr_results, px, y_axis_px, axis="x")
        if value is not None:
            ticks.append({"pixel": float(px), "value": value})
    return ticks


def _detect_y_ticks(img, y_axis, ocr_results):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    x_axis_px = y_axis["x_pixel"]
    ticks = []

    band = gray[
        y_axis["y_start"] : y_axis["y_end"],
        max(0, x_axis_px - 12) : max(1, x_axis_px - 1),
    ]
    if band.size == 0:
        return ticks
    row_darkness = np.mean(255 - band, axis=1)
    peaks = _find_peaks(row_darkness, min_distance=15)

    for p in peaks:
        py = y_axis["y_start"] + p
        value = _match_label(ocr_results, x_axis_px, py, axis="y")
        if value is not None:
            ticks.append({"pixel": float(py), "value": value})
    return ticks


def _find_peaks(signal: np.ndarray, min_distance: int) -> list[int]:
    threshold = np.mean(signal) + np.std(signal)
    candidates = [
        i
        for i in range(1, len(signal) - 1)
        if signal[i] >= threshold
        and signal[i] >= signal[i - 1]
        and signal[i] >= signal[i + 1]
    ]
    peaks: list[int] = []
    for idx in sorted(candidates, key=lambda i: signal[i], reverse=True):
        if all(abs(idx - p) >= min_distance for p in peaks):
            peaks.append(idx)
    return sorted(peaks)


def _match_label(ocr_results, px, py, axis, max_dist=40):
    best, best_dist = None, max_dist
    for item in ocr_results:
        text, center = item["text"], item["center"]
        num = _parse_number(text)
        if num is None:
            continue
        cx, cy = center
        if axis == "x":
            dist = abs(cx - px) + 0.3 * abs(cy - py)
        else:
            dist = abs(cy - py) + 0.3 * abs(cx - px)
        if dist < best_dist:
            best, best_dist = num, dist
    return best


def _parse_number(text: str):
    from ocr.postprocess import parse_number

    return parse_number(text)
