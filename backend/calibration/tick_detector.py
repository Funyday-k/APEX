import cv2
import numpy as np

from core.schemas import BBox, PlotRegion


def detect_ticks(img, axes: dict, ocr_results: list) -> dict:
    x_cv = _detect_x_ticks(img, axes["x_axis"], ocr_results)
    y_cv = _detect_y_ticks(img, axes["y_axis"], ocr_results)
    x_ocr = _ticks_from_ocr_x(ocr_results, axes["x_axis"], img.shape[0])
    y_ocr = _ticks_from_ocr_y(ocr_results, axes["y_axis"], img.shape[1])
    x_ticks = _merge_ticks(x_cv, x_ocr)
    y_ticks = _merge_ticks(y_cv, y_ocr)
    return {"x_ticks": x_ticks, "y_ticks": y_ticks}


def _merge_ticks(cv_ticks: list[dict], ocr_ticks: list[dict], merge_px: float = 12) -> list[dict]:
    merged = list(cv_ticks)
    for ot in ocr_ticks:
        if not any(abs(m["pixel"] - ot["pixel"]) < merge_px for m in merged):
            merged.append(ot)
    return sorted(merged, key=lambda t: t["pixel"])


def _ticks_from_ocr_x(ocr_results: list, x_axis: dict, img_h: int) -> list[dict]:
    if not x_axis.get("y_pixel"):
        return []
    y_line = int(x_axis["y_pixel"])
    x_start = int(x_axis.get("x_start", 0))
    x_end = int(x_axis.get("x_end", 0))
    ticks = []
    for item in ocr_results:
        num = _parse_number(item.get("text", ""))
        if num is None:
            continue
        cx, cy = item["center"]
        if not (x_start - 30 <= cx <= x_end + 30):
            continue
        if not (y_line - 5 <= cy <= min(img_h, y_line + 100)):
            continue
        ticks.append({"pixel": float(cx), "value": float(num)})
    return ticks


def _ticks_from_ocr_y(ocr_results: list, y_axis: dict, img_w: int) -> list[dict]:
    if not y_axis.get("x_pixel"):
        return []
    x_line = int(y_axis["x_pixel"])
    y_start = int(y_axis.get("y_start", 0))
    y_end = int(y_axis.get("y_end", 0))
    ticks = []
    for item in ocr_results:
        num = _parse_number(item.get("text", ""))
        if num is None:
            continue
        cx, cy = item["center"]
        if not (y_start - 30 <= cy <= y_end + 30):
            continue
        if not (max(0, x_line - 140) <= cx <= x_line + 20):
            continue
        ticks.append({"pixel": float(cy), "value": float(num)})
    return ticks


def build_tick_label_regions(
    ocr_results: list,
    axes: dict,
    img_w: int,
    img_h: int,
) -> list[PlotRegion]:
    """Cluster OCR numeric labels into x/y tick label band regions."""
    x_axis = axes.get("x_axis") or {}
    y_axis = axes.get("y_axis") or {}
    regions: list[PlotRegion] = []

    x_items = _ocr_near_x_axis(ocr_results, x_axis, img_h)
    y_items = _ocr_near_y_axis(ocr_results, y_axis, img_w)

    if len(x_items) >= 2:
        bb = _cluster_bbox(x_items, pad_x=6, pad_y=4, img_w=img_w, img_h=img_h)
        if bb:
            regions.append(
                PlotRegion(
                    kind="x_tick_labels",
                    bbox=bb,
                    source="cv",
                )
            )

    if len(y_items) >= 2:
        bb = _cluster_bbox(y_items, pad_x=4, pad_y=6, img_w=img_w, img_h=img_h)
        if bb:
            regions.append(
                PlotRegion(
                    kind="y_tick_labels",
                    bbox=bb,
                    source="cv",
                )
            )

    return regions


def _ocr_near_x_axis(ocr_results: list, x_axis: dict, img_h: int) -> list[dict]:
    if not x_axis.get("y_pixel"):
        return []
    y_line = int(x_axis["y_pixel"])
    x_start = int(x_axis.get("x_start", 0))
    x_end = int(x_axis.get("x_end", 0))
    out = []
    for item in ocr_results:
        text = item.get("text", "")
        if _parse_number(text) is None:
            continue
        cx, cy = item["center"]
        if not (x_start - 30 <= cx <= x_end + 30):
            continue
        if not (y_line <= cy <= min(img_h, y_line + 100)):
            continue
        bbox = item.get("bbox") or {}
        out.append({"center": (cx, cy), "bbox": bbox})
    return out


def _ocr_near_y_axis(ocr_results: list, y_axis: dict, img_w: int) -> list[dict]:
    if not y_axis.get("x_pixel"):
        return []
    x_line = int(y_axis["x_pixel"])
    y_start = int(y_axis.get("y_start", 0))
    y_end = int(y_axis.get("y_end", 0))
    out = []
    for item in ocr_results:
        text = item.get("text", "")
        if _parse_number(text) is None:
            continue
        cx, cy = item["center"]
        if not (y_start - 30 <= cy <= y_end + 30):
            continue
        if not (max(0, x_line - 140) <= cx <= x_line + 15):
            continue
        bbox = item.get("bbox") or {}
        out.append({"center": (cx, cy), "bbox": bbox})
    return out


def _cluster_bbox(
    items: list[dict],
    pad_x: int,
    pad_y: int,
    img_w: int,
    img_h: int,
) -> BBox | None:
    xs0, ys0, xs1, ys1 = [], [], [], []
    for item in items:
        bb = item.get("bbox") or {}
        if bb:
            xs0.append(int(bb.get("x0", bb.get("left", item["center"][0] - 10))))
            ys0.append(int(bb.get("y0", bb.get("top", item["center"][1] - 8))))
            xs1.append(int(bb.get("x1", bb.get("right", item["center"][0] + 10))))
            ys1.append(int(bb.get("y1", bb.get("bottom", item["center"][1] + 8))))
        else:
            cx, cy = item["center"]
            xs0.append(int(cx - 10))
            ys0.append(int(cy - 8))
            xs1.append(int(cx + 10))
            ys1.append(int(cy + 8))

    x0 = max(0, min(xs0) - pad_x)
    y0 = max(0, min(ys0) - pad_y)
    x1 = min(img_w, max(xs1) + pad_x)
    y1 = min(img_h, max(ys1) + pad_y)
    if x1 <= x0 or y1 <= y0:
        return None
    conf = min(0.95, 0.55 + 0.08 * len(items))
    return BBox(x0=x0, y0=y0, x1=x1, y1=y1, confidence=conf)


def _detect_x_ticks(img, x_axis, ocr_results):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    y_axis_px = int(x_axis["y_pixel"])
    ticks = []
    x_start = int(x_axis["x_start"])
    x_end = int(x_axis["x_end"])

    band_h = 16
    band = gray[y_axis_px + 1 : y_axis_px + band_h, x_start:x_end]
    if band.size == 0:
        return ticks
    col_darkness = np.mean(255 - band, axis=0)
    peaks = _find_peaks(col_darkness, min_distance=12)

    for p in peaks:
        px = x_start + p
        value = _match_label(ocr_results, px, y_axis_px, axis="x", max_dist=55)
        if value is not None:
            ticks.append({"pixel": float(px), "value": value})
    return ticks


def _detect_y_ticks(img, y_axis, ocr_results):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    x_axis_px = int(y_axis["x_pixel"])
    ticks = []
    y_start = int(y_axis["y_start"])
    y_end = int(y_axis["y_end"])

    band_w = 16
    band = gray[y_start:y_end, max(0, x_axis_px - band_w) : max(1, x_axis_px - 1)]
    if band.size == 0:
        return ticks
    row_darkness = np.mean(255 - band, axis=1)
    peaks = _find_peaks(row_darkness, min_distance=12)

    for p in peaks:
        py = y_start + p
        value = _match_label(ocr_results, x_axis_px, py, axis="y", max_dist=55)
        if value is not None:
            ticks.append({"pixel": float(py), "value": value})
    return ticks


def _find_peaks(signal: np.ndarray, min_distance: int) -> list[int]:
    threshold = np.mean(signal) + 0.75 * np.std(signal)
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
