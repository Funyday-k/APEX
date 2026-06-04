"""Fuse VLM region bboxes with CV plot area, axes, and OCR clusters."""

from __future__ import annotations

from core.schemas import BBox, PlotRegion, PlotRegions, RegionKind

VALID_REGION_KINDS: frozenset[str] = frozenset(
    {
        "plot_area",
        "legend",
        "x_axis",
        "y_axis",
        "x_tick_labels",
        "y_tick_labels",
        "title",
        "colorbar",
        "other_text",
    }
)

EXCLUDE_MASK_KINDS: frozenset[RegionKind] = frozenset(
    {
        "legend",
        "x_tick_labels",
        "y_tick_labels",
        "title",
        "other_text",
        "colorbar",
    }
)


def _clamp_bbox(x0: int, y0: int, x1: int, y1: int, w: int, h: int) -> BBox | None:
    x0, x1 = max(0, min(x0, x1)), min(w, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(h, max(y0, y1))
    if x1 <= x0 or y1 <= y0:
        return None
    return BBox(x0=x0, y0=y0, x1=x1, y1=y1)


def bbox_iou(a: BBox, b: BBox) -> float:
    ix0 = max(a.x0, b.x0)
    iy0 = max(a.y0, b.y0)
    ix1 = min(a.x1, b.x1)
    iy1 = min(a.y1, b.y1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = (a.x1 - a.x0) * (a.y1 - a.y0)
    area_b = (b.x1 - b.x0) * (b.y1 - b.y0)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _fuse_bboxes(a: BBox, b: BBox, w: int, h: int, weight_a: float = 0.5) -> BBox | None:
    """Weighted average of two bboxes, clamped to image."""
    wa = max(0.05, min(0.95, weight_a))
    wb = 1.0 - wa
    x0 = int(round(a.x0 * wa + b.x0 * wb))
    y0 = int(round(a.y0 * wa + b.y0 * wb))
    x1 = int(round(a.x1 * wa + b.x1 * wb))
    y1 = int(round(a.y1 * wa + b.y1 * wb))
    fused = _clamp_bbox(x0, y0, x1, y1, w, h)
    if fused is None:
        return None
    fused.confidence = min(1.0, (a.confidence * wa + b.confidence * wb) + 0.05)
    return fused


def _norm_to_pixel(
    bbox: dict, img_w: int, img_h: int, coord_space: str | None
) -> BBox | None:
    x0 = float(bbox.get("x0", bbox.get("left", 0)))
    y0 = float(bbox.get("y0", bbox.get("top", 0)))
    x1 = float(bbox.get("x1", bbox.get("right", x0)))
    y1 = float(bbox.get("y1", bbox.get("bottom", y0)))
    if coord_space == "normalized" or (0 <= x0 <= 1 and 0 <= x1 <= 1 and x1 <= 1.01):
        x0, x1 = x0 * img_w, x1 * img_w
        y0, y1 = y0 * img_h, y1 * img_h
    return _clamp_bbox(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)), img_w, img_h)


def parse_vlm_regions(raw: dict, img_w: int, img_h: int) -> PlotRegions:
    """Parse VLM segment_regions JSON into PlotRegions."""
    regions: list[PlotRegion] = []
    coord_space = raw.get("coord_space", "pixel")
    for item in raw.get("regions", []) or []:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind") or item.get("type")
        if kind not in VALID_REGION_KINDS:
            continue
        bbox_raw = item.get("bbox") or item
        if not isinstance(bbox_raw, dict):
            continue
        bb = _norm_to_pixel(bbox_raw, img_w, img_h, coord_space)
        if bb is None:
            continue
        conf = float(item.get("confidence", bb.confidence))
        bb.confidence = max(0.0, min(1.0, conf))
        regions.append(
            PlotRegion(
                kind=kind,
                bbox=bb,
                label=item.get("label"),
                source="vlm",
            )
        )
    pr = PlotRegions(
        regions=regions,
        image_width=img_w,
        image_height=img_h,
        source="vlm",
    )
    vlm_w = raw.get("image_width")
    vlm_h = raw.get("image_height")
    if (
        isinstance(vlm_w, (int, float))
        and isinstance(vlm_h, (int, float))
        and vlm_w > 0
        and vlm_h > 0
        and (int(vlm_w) != img_w or int(vlm_h) != img_h)
    ):
        sx = img_w / float(vlm_w)
        sy = img_h / float(vlm_h)
        scaled = []
        for r in pr.regions:
            b = r.bbox
            bb = _clamp_bbox(
                int(round(b.x0 * sx)),
                int(round(b.y0 * sy)),
                int(round(b.x1 * sx)),
                int(round(b.y1 * sy)),
                img_w,
                img_h,
            )
            if bb:
                bb.confidence = b.confidence
                scaled.append(r.model_copy(update={"bbox": bb}))
        pr.regions = scaled
    return pr


def merge_plot_area(
    regions: PlotRegions,
    plot_area: dict,
    img_w: int,
    img_h: int,
) -> PlotRegions:
    """Fuse or add plot_area from Hough detection."""
    if not plot_area.get("detected"):
        regions.image_width = img_w
        regions.image_height = img_h
        return regions

    bb = _clamp_bbox(
        int(plot_area["x0"]),
        int(plot_area["y0"]),
        int(plot_area["x1"]),
        int(plot_area["y1"]),
        img_w,
        img_h,
    )
    if bb is None:
        regions.image_width = img_w
        regions.image_height = img_h
        return regions

    cv_conf = 0.75 if plot_area.get("detected") else 0.4
    bb.confidence = cv_conf
    existing = [r for r in regions.regions if r.kind == "plot_area"]

    if not existing:
        regions.regions.append(PlotRegion(kind="plot_area", bbox=bb, source="cv"))
    else:
        vlm_region = existing[0]
        iou = bbox_iou(vlm_region.bbox, bb)
        if iou < 0.25:
            # Large disagreement: prefer CV when VLM confidence is low, else fuse toward intersection
            if vlm_region.bbox.confidence < 0.65:
                regions.regions = [r for r in regions.regions if r.kind != "plot_area"]
                regions.regions.append(
                    PlotRegion(kind="plot_area", bbox=bb, source="cv")
                )
            else:
                fused = _fuse_bboxes(vlm_region.bbox, bb, img_w, img_h, weight_a=0.35)
                if fused:
                    regions.regions = [r for r in regions.regions if r.kind != "plot_area"]
                    regions.regions.append(
                        PlotRegion(kind="plot_area", bbox=fused, source="fused")
                    )
        elif iou < 0.7:
            fused = _fuse_bboxes(vlm_region.bbox, bb, img_w, img_h, weight_a=0.45)
            if fused:
                regions.regions = [r for r in regions.regions if r.kind != "plot_area"]
                regions.regions.append(
                    PlotRegion(kind="plot_area", bbox=fused, source="fused")
                )
        else:
            # High IoU but CV may extend right/bottom — union expand when CV is wider
            vlm_bb = vlm_region.bbox
            expanded = _clamp_bbox(
                min(vlm_bb.x0, bb.x0),
                min(vlm_bb.y0, bb.y0),
                max(vlm_bb.x1, bb.x1),
                max(vlm_bb.y1, bb.y1),
                img_w,
                img_h,
            )
            if expanded and (expanded.x1 > vlm_bb.x1 or expanded.y1 > vlm_bb.y1):
                expanded.confidence = max(vlm_bb.confidence, bb.confidence)
                regions.regions = [r for r in regions.regions if r.kind != "plot_area"]
                regions.regions.append(
                    PlotRegion(kind="plot_area", bbox=expanded, source="fused")
                )

    regions.image_width = img_w
    regions.image_height = img_h
    if any(r.source == "fused" for r in regions.regions if r.kind == "plot_area"):
        regions.source = "fused"
    return regions


def merge_axis_regions(
    regions: PlotRegions,
    axis_geometry: dict,
    img_w: int,
    img_h: int,
) -> PlotRegions:
    """Add or refine x/y axis regions from CV axis geometry."""
    x_axis = axis_geometry.get("x_axis") or {}
    y_axis = axis_geometry.get("y_axis") or {}
    x_bbox_raw = axis_geometry.get("x_axis_bbox")
    y_bbox_raw = axis_geometry.get("y_axis_bbox")

    cv_regions: list[PlotRegion] = []

    if x_bbox_raw:
        bb = _clamp_bbox(
            int(x_bbox_raw["x0"]),
            int(x_bbox_raw["y0"]),
            int(x_bbox_raw["x1"]),
            int(x_bbox_raw["y1"]),
            img_w,
            img_h,
        )
        if bb:
            bb.confidence = float(x_axis.get("confidence", 0.7))
            cv_regions.append(PlotRegion(kind="x_axis", bbox=bb, source="cv"))
    elif x_axis.get("y_pixel") is not None:
        y_px = int(x_axis["y_pixel"])
        bb = _clamp_bbox(
            int(x_axis.get("x_start", 0)),
            max(0, y_px - 4),
            int(x_axis.get("x_end", img_w)),
            min(img_h, y_px + 4),
            img_w,
            img_h,
        )
        if bb:
            bb.confidence = float(x_axis.get("confidence", 0.6))
            cv_regions.append(PlotRegion(kind="x_axis", bbox=bb, source="cv"))

    if y_bbox_raw:
        bb = _clamp_bbox(
            int(y_bbox_raw["x0"]),
            int(y_bbox_raw["y0"]),
            int(y_bbox_raw["x1"]),
            int(y_bbox_raw["y1"]),
            img_w,
            img_h,
        )
        if bb:
            bb.confidence = float(y_axis.get("confidence", 0.7))
            cv_regions.append(PlotRegion(kind="y_axis", bbox=bb, source="cv"))
    elif y_axis.get("x_pixel") is not None:
        x_px = int(y_axis["x_pixel"])
        bb = _clamp_bbox(
            max(0, x_px - 4),
            int(y_axis.get("y_start", 0)),
            min(img_w, x_px + 4),
            int(y_axis.get("y_end", img_h)),
            img_w,
            img_h,
        )
        if bb:
            bb.confidence = float(y_axis.get("confidence", 0.6))
            cv_regions.append(PlotRegion(kind="y_axis", bbox=bb, source="cv"))

    for cv_r in cv_regions:
        existing = [r for r in regions.regions if r.kind == cv_r.kind]
        if not existing:
            regions.regions.append(cv_r)
            continue
        vlm_r = existing[0]
        iou = bbox_iou(vlm_r.bbox, cv_r.bbox)
        if iou < 0.3 or vlm_r.bbox.confidence < cv_r.bbox.confidence:
            regions.regions = [r for r in regions.regions if r.kind != cv_r.kind]
            if iou >= 0.15:
                fused = _fuse_bboxes(vlm_r.bbox, cv_r.bbox, img_w, img_h, weight_a=0.4)
                if fused:
                    regions.regions.append(
                        PlotRegion(kind=cv_r.kind, bbox=fused, source="fused")
                    )
                    continue
            regions.regions.append(cv_r)

    return regions


def merge_tick_label_regions(
    regions: PlotRegions,
    tick_regions: list[PlotRegion],
) -> PlotRegions:
    """Add OCR-cluster tick label regions when VLM did not detect them."""
    for tr in tick_regions:
        existing = [r for r in regions.regions if r.kind == tr.kind]
        if not existing:
            regions.regions.append(tr)
        elif existing[0].bbox.confidence < tr.bbox.confidence:
            regions.regions = [r for r in regions.regions if r.kind != tr.kind]
            regions.regions.append(tr)
    return regions


def regions_for_mask(regions: PlotRegions | None) -> list[PlotRegion]:
    if not regions:
        return []
    return [r for r in regions.regions if r.kind in EXCLUDE_MASK_KINDS]


def point_in_regions(px: float, py: float, regions: list[PlotRegion], kinds: frozenset | None = None) -> bool:
    kinds = kinds or EXCLUDE_MASK_KINDS
    for r in regions:
        if r.kind not in kinds:
            continue
        b = r.bbox
        if b.x0 <= px <= b.x1 and b.y0 <= py <= b.y1:
            return True
    return False


def chart_metadata_from_semantics(semantics: dict) -> dict:
    """Build ChartMetadata-compatible dict from VLM semantics."""
    return {
        "title": semantics.get("title"),
        "x_label": semantics.get("x_label"),
        "y_label": semantics.get("y_label"),
        "x_quantity": semantics.get("x_quantity"),
        "y_quantity": semantics.get("y_quantity"),
        "x_unit": semantics.get("x_unit"),
        "y_unit": semantics.get("y_unit"),
        "x_scale": semantics.get("x_scale") or "linear",
        "y_scale": semantics.get("y_scale") or "linear",
        "legend": semantics.get("legend") or [],
    }


def axis_confidence_from_geometry(axis_geometry: dict, plot_area: dict) -> dict:
    return {
        "x_axis": float((axis_geometry.get("x_axis") or {}).get("confidence", 0.5)),
        "y_axis": float((axis_geometry.get("y_axis") or {}).get("confidence", 0.5)),
        "plot_area": 0.75 if plot_area.get("detected") else 0.35,
    }
