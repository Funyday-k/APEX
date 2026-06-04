"""Composite chart case detection and per-case extraction."""

from __future__ import annotations

from core.schemas import ChartType, DataSeries, ExtractionResult
from extractors.line_chart import LineChartExtractor
from extractors.scatter import ScatterExtractor


def normalize_case(raw: dict, img_w: int = 0, img_h: int = 0) -> dict:
    rep = str(raw.get("representation", "scatter")).lower()
    if rep not in ("line", "scatter", "band"):
        rep = "scatter"
    color = raw.get("color_hex") or raw.get("color") or "#3388ff"
    if isinstance(color, str) and not color.startswith("#"):
        color = "#3388ff"
    out = {
        "label": str(raw.get("label") or "series"),
        "color_hex": color,
        "representation": rep,
        "notes": raw.get("notes"),
    }
    bb = raw.get("sub_bbox")
    if isinstance(bb, dict) and img_w > 0 and img_h > 0:
        cs = bb.get("coord_space", "normalized")
        x0 = float(bb.get("x0", 0))
        y0 = float(bb.get("y0", 0))
        x1 = float(bb.get("x1", 1))
        y1 = float(bb.get("y1", 1))
        if cs == "normalized" or max(x0, y0, x1, y1) <= 1.01:
            x0, x1 = x0 * img_w, x1 * img_w
            y0, y1 = y0 * img_h, y1 * img_h
        out["sub_bbox"] = {
            "x0": int(max(0, min(x0, x1))),
            "y0": int(max(0, min(y0, y1))),
            "x1": int(min(img_w, max(x0, x1))),
            "y1": int(min(img_h, max(y0, y1))),
        }
    elif isinstance(bb, dict):
        out["sub_bbox"] = {
            "x0": int(bb.get("x0", 0)),
            "y0": int(bb.get("y0", 0)),
            "x1": int(bb.get("x1", img_w or 1)),
            "y1": int(bb.get("y1", img_h or 1)),
        }
    return out


def build_cases(semantics: dict | None, vlm_raw: dict | None, img_w: int, img_h: int) -> list[dict]:
    """Build extraction cases from VLM or semantics legend fallback."""
    semantics = semantics or {}
    vlm_raw = vlm_raw or {}
    raw_list = vlm_raw.get("cases")
    if isinstance(raw_list, list) and len(raw_list) >= 1:
        return [normalize_case(c, img_w, img_h) for c in raw_list if isinstance(c, dict)]

    legend = semantics.get("legend") or []
    series_colors = semantics.get("series_colors") or {}
    if not legend and isinstance(series_colors, dict):
        legend = list(series_colors.keys())

    cases: list[dict] = []
    for label in legend:
        if not label:
            continue
        color = series_colors.get(label, "#3388ff") if isinstance(series_colors, dict) else "#3388ff"
        rep = "scatter"
        lbl = str(label).lower()
        if "band" in lbl or "error" in lbl or "shade" in lbl:
            rep = "band"
        elif "line" in lbl or "curve" in lbl or "theory" in lbl:
            rep = "line"
        cases.append(
            normalize_case(
                {"label": str(label), "color_hex": color, "representation": rep},
                img_w,
                img_h,
            )
        )

    if not cases:
        cases.append(
            normalize_case(
                {"label": "series_1", "color_hex": "#3388ff", "representation": "scatter"},
                img_w,
                img_h,
            )
        )
    return cases


def _crop_image(img, sub_bbox: dict | None):
    if not sub_bbox:
        return img
    h, w = img.shape[:2]
    x0 = max(0, int(sub_bbox.get("x0", 0)))
    y0 = max(0, int(sub_bbox.get("y0", 0)))
    x1 = min(w, int(sub_bbox.get("x1", w)))
    y1 = min(h, int(sub_bbox.get("y1", h)))
    if x1 <= x0 + 4 or y1 <= y0 + 4:
        return img
    return img[y0:y1, x0:x1].copy()


def extract_cases_on_image(
    img,
    calibrator,
    cases: list[dict],
    plot_regions=None,
    extract_options: dict | None = None,
) -> list[DataSeries]:
    """Run per-case extractors and merge series list."""
    extract_options = extract_options or {}
    all_series: list[DataSeries] = []
    for case in cases:
        rep = case.get("representation", "scatter")
        color = case.get("color_hex")
        colors = [color] if color else None
        sub = _crop_image(img, case.get("sub_bbox"))
        label = case.get("label") or "series"

        if rep == "scatter":
            extractor = ScatterExtractor()
        else:
            extractor = LineChartExtractor()

        kw = {"regions": plot_regions, **extract_options}
        try:
            series_list = extractor.extract(sub, calibrator, colors, **kw)
        except TypeError:
            series_list = extractor.extract(sub, calibrator, colors)

        for s in series_list:
            s.name = label
            if rep == "band" and hasattr(s, "model_copy"):
                s = s.model_copy(update={"representation": "continuous"})
            elif rep == "band":
                s.representation = "continuous"
            all_series.append(s)

    return all_series


def build_extraction_result(
    series: list[DataSeries],
    semantics: dict | None,
    chart_type: ChartType = ChartType.SCATTER,
) -> ExtractionResult:
    sem = semantics or {}
    confs = [s.confidence for s in series if s.points]
    overall = float(sum(confs) / len(confs)) if confs else 0.5
    return ExtractionResult(
        chart_type=chart_type,
        series=series,
        title=sem.get("title"),
        x_label=sem.get("x_label"),
        y_label=sem.get("y_label"),
        legend=sem.get("legend") or [],
        overall_confidence=overall,
    )
