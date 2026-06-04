"""CV-based legend region detection to complement VLM segmentation."""

from __future__ import annotations

import cv2
import numpy as np

from core.schemas import BBox, PlotRegion


def _search_rois(plot_area: dict, w: int, h: int) -> list[dict]:
    """Candidate ROIs for legend search (fractions of plot or image)."""
    if not plot_area.get("detected"):
        return [
            {"x0": int(w * 0.55), "y0": 0, "x1": w - 1, "y1": int(h * 0.35), "name": "global_ur"},
            {"x0": int(w * 0.55), "y0": int(h * 0.55), "x1": w - 1, "y1": h - 1, "name": "global_lr"},
            {"x0": 0, "y0": 0, "x1": int(w * 0.45), "y1": int(h * 0.35), "name": "global_ul"},
            {"x0": 0, "y0": int(h * 0.55), "x1": int(w * 0.45), "y1": h - 1, "name": "global_ll"},
        ]
    px0, py0, px1, py1 = (
        int(plot_area["x0"]),
        int(plot_area["y0"]),
        int(plot_area["x1"]),
        int(plot_area["y1"]),
    )
    pw, ph = max(1, px1 - px0), max(1, py1 - py0)
    margin_x = int(pw * 0.08)
    margin_y = int(ph * 0.05)
    return [
        {
            "x0": max(0, px0 + int(pw * 0.45)),
            "y0": max(0, py0 - margin_y),
            "x1": min(w - 1, px1 + margin_x),
            "y1": min(h - 1, py0 + int(ph * 0.45)),
            "name": "plot_ur",
        },
        {
            "x0": max(0, px0 + int(pw * 0.45)),
            "y0": max(0, py0 + int(ph * 0.55)),
            "x1": min(w - 1, px1 + margin_x),
            "y1": min(h - 1, py1 + margin_y),
            "name": "plot_lr",
        },
        {
            "x0": max(0, px0 - margin_x),
            "y0": max(0, py0 - margin_y),
            "x1": min(w - 1, px0 + int(pw * 0.45)),
            "y1": min(h - 1, py0 + int(ph * 0.45)),
            "name": "plot_ul",
        },
        {
            "x0": max(0, px0 - margin_x),
            "y0": max(0, py0 + int(ph * 0.55)),
            "x1": min(w - 1, px0 + int(pw * 0.45)),
            "y1": min(h - 1, py1 + margin_y),
            "name": "plot_ll",
        },
        {
            "x0": max(0, px1 + 2),
            "y0": max(0, py0),
            "x1": min(w - 1, px1 + int(pw * 0.35) + margin_x),
            "y1": min(h - 1, py1),
            "name": "outside_right",
        },
        {
            "x0": max(0, px0),
            "y0": min(h - 1, py1 + 2),
            "x1": min(w - 1, px1),
            "y1": min(h - 1, py1 + int(ph * 0.25) + margin_y),
            "name": "outside_bottom",
        },
    ]


def _legend_border_bbox(roi_gray: np.ndarray, offset_x: int, offset_y: int) -> tuple[int, int, int, int] | None:
    """Detect rectangular legend frame via edge/contour analysis."""
    edges = cv2.Canny(roi_gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rh, rw = roi_gray.shape[:2]
    best = None
    best_score = 0.0
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = bw * bh
        if area < 400 or area > rw * rh * 0.85:
            continue
        if bw < 40 or bh < 16:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        rect_score = 1.0 if len(approx) == 4 else 0.6
        aspect = bw / max(bh, 1)
        if aspect < 0.8 or aspect > 12:
            continue
        score = rect_score * min(1.0, area / (rw * rh * 0.3))
        if score > best_score:
            best_score = score
            best = (x + offset_x, y + offset_y, x + bw + offset_x, y + bh + offset_y)
    return best


def _marker_points_in_roi(
    roi: np.ndarray, search: dict, img_area_scale: float
) -> list[tuple[float, float]]:
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1]
    max_area = max(800, int(800 * img_area_scale))
    max_dim = max(30, int(30 * np.sqrt(img_area_scale)))
    blob_mask = ((sat > 35) & (gray < 245)).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    blob_mask = cv2.morphologyEx(blob_mask, cv2.MORPH_OPEN, kernel)
    n, _, stats, centroids = cv2.connectedComponentsWithStats(blob_mask, connectivity=8)
    pts = []
    min_area = max(4, int(6 * img_area_scale))
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        bw = stats[i, cv2.CC_STAT_WIDTH]
        bh = stats[i, cv2.CC_STAT_HEIGHT]
        if min_area <= area <= max_area and bw <= max_dim and bh <= max_dim:
            cx, cy = centroids[i]
            pts.append((float(cx + search["x0"]), float(cy + search["y0"])))
    return pts


def _bbox_from_elements(
    marker_pts: list[tuple[float, float]],
    text_boxes: list[tuple[int, int, int, int]],
    border: tuple[int, int, int, int] | None,
    img_w: int,
    img_h: int,
    img_area_scale: float,
) -> tuple[int, int, int, int] | None:
    if border:
        return border
    if not marker_pts and not text_boxes:
        return None
    pad_x = int(12 + 8 * np.sqrt(img_area_scale))
    pad_y = int(12 + 4 * np.sqrt(img_area_scale))
    text_pad_right = int(60 + 20 * np.sqrt(img_area_scale))
    xs, ys, xs1, ys1 = [], [], [], []
    for cx, cy in marker_pts:
        xs.append(int(cx - pad_x))
        ys.append(int(cy - pad_y))
        xs1.append(int(cx + text_pad_right))
        ys1.append(int(cy + pad_y))
    for bb in text_boxes:
        xs.append(bb[0])
        ys.append(bb[1])
        xs1.append(bb[2])
        ys1.append(bb[3])
    x0 = max(0, min(xs) - 8)
    y0 = max(0, min(ys) - 8)
    x1 = min(img_w, max(xs1) + 8)
    y1 = min(img_h, max(ys1) + 8)
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def _score_candidate(
    bbox: tuple[int, int, int, int],
    n_markers: int,
    n_text: int,
    has_border: bool,
) -> float:
    x0, y0, x1, y1 = bbox
    area = (x1 - x0) * (y1 - y0)
    if area < 100:
        return 0.0
    score = 0.35
    if has_border:
        score += 0.25
    score += min(0.25, 0.08 * n_markers)
    score += min(0.2, 0.06 * n_text)
    if n_markers >= 2 or (n_markers >= 1 and n_text >= 1):
        score += 0.1
    return min(0.95, score)


def detect_legend_regions(
    img: np.ndarray,
    plot_area: dict,
    ocr_results: list | None = None,
    img_w: int | None = None,
    img_h: int | None = None,
) -> list[PlotRegion]:
    """
    Heuristic legend detector: scan multiple ROIs, score candidates,
  return up to two legend boxes.
    """
    h, w = img.shape[:2]
    img_w = img_w or w
    img_h = img_h or h
    img_area_scale = (img_w * img_h) / (500.0 * 400.0)

    candidates: list[tuple[float, PlotRegion]] = []

    for search in _search_rois(plot_area, w, h):
        roi = img[search["y0"] : search["y1"], search["x0"] : search["x1"]]
        if roi.size == 0:
            continue
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        border = _legend_border_bbox(gray, search["x0"], search["y0"])
        marker_pts = _marker_points_in_roi(roi, search, img_area_scale)
        text_boxes = _legend_text_boxes(ocr_results, search, w, h)
        if len(marker_pts) < 1 and len(text_boxes) < 1 and not border:
            continue
        bbox = _bbox_from_elements(
            marker_pts, text_boxes, border, img_w, img_h, img_area_scale
        )
        if not bbox:
            continue
        conf = _score_candidate(bbox, len(marker_pts), len(text_boxes), border is not None)
        if conf < 0.42:
            continue
        x0, y0, x1, y1 = bbox
        candidates.append(
            (
                conf,
                PlotRegion(
                    kind="legend",
                    bbox=BBox(x0=x0, y0=y0, x1=x1, y1=y1, confidence=conf),
                    label=f"cv_legend_{search.get('name', 'roi')}",
                    source="cv",
                ),
            )
        )

    if not candidates:
        return []

    candidates.sort(key=lambda c: c[0], reverse=True)
    # NMS: drop heavy overlaps, keep up to 2
    kept: list[PlotRegion] = []
    from preprocessing.region_fusion import bbox_iou

    for _, reg in candidates:
        if all(bbox_iou(reg.bbox, k.bbox) < 0.55 for k in kept):
            kept.append(reg)
        if len(kept) >= 2:
            break
    return kept


def _legend_text_boxes(
    ocr_results: list | None, search: dict, img_w: int, img_h: int
) -> list[tuple[int, int, int, int]]:
    if not ocr_results:
        return []
    boxes = []
    for item in ocr_results:
        text = (item.get("text") or "").strip()
        if len(text) < 1 or len(text) > 80:
            continue
        cx, cy = item.get("center", (0, 0))
        if not (search["x0"] <= cx <= search["x1"] and search["y0"] <= cy <= search["y1"]):
            continue
        bb = item.get("bbox") or {}
        if bb:
            x0 = int(bb.get("x0", bb.get("left", cx - 10)))
            y0 = int(bb.get("y0", bb.get("top", cy - 8)))
            x1 = int(bb.get("x1", bb.get("right", cx + 10)))
            y1 = int(bb.get("y1", bb.get("bottom", cy + 8)))
        else:
            x0, y0, x1, y1 = int(cx - 10), int(cy - 8), int(cx + 10), int(cy + 8)
        boxes.append((max(0, x0), max(0, y0), min(img_w, x1), min(img_h, y1)))
    return boxes


def merge_legend_regions(regions, cv_legends: list[PlotRegion], img_w: int, img_h: int):
    """Merge CV legends with VLM legends using IoU pairing (supports multiple)."""
    from preprocessing.region_fusion import bbox_iou

    if not cv_legends:
        return regions

    vlm_legends = [r for r in regions.regions if r.kind == "legend"]
    other = [r for r in regions.regions if r.kind != "legend"]
    used_cv: set[int] = set()
    fused: list[PlotRegion] = []

    for vlm_r in vlm_legends:
        best_i = -1
        best_iou = 0.0
        for i, cv_r in enumerate(cv_legends):
            if i in used_cv:
                continue
            iou = bbox_iou(vlm_r.bbox, cv_r.bbox)
            if iou > best_iou:
                best_iou = iou
                best_i = i
        if best_i >= 0 and best_iou >= 0.15:
            cv_r = cv_legends[best_i]
            used_cv.add(best_i)
            b1, b2 = vlm_r.bbox, cv_r.bbox
            if best_iou < 0.2 or b1.confidence < b2.confidence:
                x0 = max(0, min(b1.x0, b2.x0))
                y0 = max(0, min(b1.y0, b2.y0))
                x1 = min(img_w, max(b1.x1, b2.x1))
                y1 = min(img_h, max(b1.y1, b2.y1))
                merged_bb = BBox(
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    confidence=max(b1.confidence, b2.confidence),
                )
                fused.append(
                    PlotRegion(
                        kind="legend",
                        bbox=merged_bb,
                        label="fused_legend",
                        source="fused",
                    )
                )
            else:
                fused.append(vlm_r)
        else:
            fused.append(vlm_r)

    for i, cv_r in enumerate(cv_legends):
        if i in used_cv:
            continue
        if not any(bbox_iou(cv_r.bbox, f.bbox) > 0.35 for f in fused):
            fused.append(cv_r)

    regions.regions = other + fused
    return regions
