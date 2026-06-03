"""Fuse VLM region bboxes with CV plot area and OCR clusters."""

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
        "x_axis",
        "y_axis",
    }
)


def _clamp_bbox(x0: int, y0: int, x1: int, y1: int, w: int, h: int) -> BBox | None:
    x0, x1 = max(0, min(x0, x1)), min(w, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(h, max(y0, y1))
    if x1 <= x0 or y1 <= y0:
        return None
    return BBox(x0=x0, y0=y0, x1=x1, y1=y1)


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
            PlotRegion(kind=kind, bbox=bb, label=item.get("label"))
        )
    return PlotRegions(
        regions=regions,
        image_width=img_w,
        image_height=img_h,
        source="vlm",
    )


def merge_plot_area(
    regions: PlotRegions,
    plot_area: dict,
    img_w: int,
    img_h: int,
) -> PlotRegions:
    """Add or refine plot_area from Hough detection."""
    if plot_area.get("detected"):
        bb = _clamp_bbox(
            int(plot_area["x0"]),
            int(plot_area["y0"]),
            int(plot_area["x1"]),
            int(plot_area["y1"]),
            img_w,
            img_h,
        )
        if bb:
            existing = [r for r in regions.regions if r.kind == "plot_area"]
            if not existing:
                regions.regions.append(PlotRegion(kind="plot_area", bbox=bb))
    regions.image_width = img_w
    regions.image_height = img_h
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
