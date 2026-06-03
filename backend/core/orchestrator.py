from calibration.axis_detector import detect_axes
from calibration.calibrator import Calibrator
from calibration.tick_detector import detect_ticks
from classification.classifier import classify_chart
from core.calibration_scale import scale_calibration
from core.schemas import (
    CalibrationConfig,
    ChartType,
    ExtractionResult,
    HeatmapOptions,
    PlotRegions,
)
from extractors import get_extractor
from ocr.ocr_engine import OCREngine
from preprocessing.enhance import enhance, upscale_if_small
from preprocessing.loader import load_image
from preprocessing.plot_area import detect_plot_area
from preprocessing.region_fusion import (
    chart_metadata_from_semantics,
    merge_plot_area,
    parse_vlm_regions,
)
from validation.cross_validator import CrossValidator
from validation.point_audit import (
    format_detected_summary,
    format_regions_summary,
    format_semantics_summary,
    parse_audit_removals,
)
from vlm.provider import get_vlm_provider


def _parse_regions_payload(raw: dict | PlotRegions | None, img_w: int, img_h: int) -> PlotRegions | None:
    if raw is None:
        return None
    if isinstance(raw, PlotRegions):
        return raw
    if isinstance(raw, dict) and raw.get("regions") is not None:
        if isinstance(raw["regions"], list) and raw.get("image_width"):
            try:
                return PlotRegions.model_validate(raw)
            except Exception:
                pass
        return parse_vlm_regions(raw, img_w, img_h)
    return None


def _scale_regions(regions: PlotRegions | None, scale: float) -> PlotRegions | None:
    if regions is None or scale == 1.0:
        return regions
    scaled = []
    for r in regions.regions:
        b = r.bbox
        scaled.append(
            r.model_copy(
                update={
                    "bbox": b.model_copy(
                        update={
                            "x0": int(round(b.x0 * scale)),
                            "y0": int(round(b.y0 * scale)),
                            "x1": int(round(b.x1 * scale)),
                            "y1": int(round(b.y1 * scale)),
                        }
                    )
                }
            )
        )
    return PlotRegions(
        regions=scaled,
        image_width=int(round(regions.image_width * scale)),
        image_height=int(round(regions.image_height * scale)),
        source=regions.source,
    )


class Orchestrator:
    def __init__(self):
        self.ocr = OCREngine()
        self.vlm = get_vlm_provider()
        self.validator = CrossValidator()

    async def auto_analyze(self, image_bytes: bytes) -> dict:
        img = load_image(image_bytes)
        img = enhance(img)
        h, w = img.shape[:2]

        plot_area = detect_plot_area(img)
        chart_type = await classify_chart(img, self.vlm)
        ocr_results = self.ocr.extract(img)
        semantics = await self.vlm.analyze_semantics(image_bytes)

        regions_raw = await self.vlm.segment_regions(image_bytes)
        regions = parse_vlm_regions(regions_raw, w, h) if regions_raw else PlotRegions(
            image_width=w, image_height=h, source="none"
        )
        regions = merge_plot_area(regions, plot_area, w, h)

        axes = detect_axes(img, plot_area)
        ticks = detect_ticks(img, axes, ocr_results)
        chart_metadata = chart_metadata_from_semantics(semantics)

        return {
            "chart_type": chart_type.value if hasattr(chart_type, "value") else chart_type,
            "plot_area": plot_area,
            "ocr": ocr_results,
            "semantics": semantics,
            "suggested_calibration": ticks,
            "regions": regions.model_dump(mode="json"),
            "chart_metadata": chart_metadata,
        }

    async def extract(
        self,
        image_bytes: bytes,
        chart_type: ChartType,
        calibration: CalibrationConfig,
        series_colors: list[str] | None = None,
        heatmap_options: HeatmapOptions | None = None,
        semantics: dict | None = None,
        regions: dict | PlotRegions | None = None,
    ) -> ExtractionResult:
        img = load_image(image_bytes)
        orig_h, orig_w = img.shape[:2]
        img = enhance(img)
        img_work, scale = self._prepare_working_image(img)

        cal_work = scale_calibration(calibration, scale) if scale != 1.0 else calibration

        if not series_colors and semantics:
            series_colors = self._series_colors_from_semantics(semantics)

        plot_regions = _parse_regions_payload(regions, orig_w, orig_h)
        if plot_regions and scale != 1.0:
            plot_regions = _scale_regions(plot_regions, scale)

        extractor = get_extractor(chart_type)
        calibrator = Calibrator(cal_work)

        extract_kw = {"regions": plot_regions}
        if chart_type == ChartType.HEATMAP:
            cv_series = extractor.extract(
                img_work,
                calibrator,
                series_colors,
                heatmap_options=heatmap_options,
            )
        else:
            cv_series = extractor.extract(
                img_work, calibrator, series_colors, **extract_kw
            )

        if semantics is None:
            semantics = await self.vlm.analyze_semantics(image_bytes)
        semantics = dict(semantics)
        semantics["chart_type"] = chart_type.value

        if plot_regions is None:
            h_work, w_work = img_work.shape[:2]
            regions_raw = await self.vlm.segment_regions(image_bytes)
            if regions_raw:
                pr = parse_vlm_regions(regions_raw, orig_w, orig_h)
                plot_regions = _scale_regions(pr, scale) if scale != 1.0 else pr
                plot_regions.image_width = w_work
                plot_regions.image_height = h_work

        result = self.validator.validate(cv_series, semantics, img_work)
        result.chart_type = chart_type
        result.regions = plot_regions

        fit_curves = getattr(extractor, "_last_fit_curves", [])
        if fit_curves:
            result.metadata["fit_curves"] = [
                f.model_dump(mode="json") if hasattr(f, "model_dump") else f for f in fit_curves
            ]

        detected = getattr(extractor, "_last_detected_pixels", {})
        if detected and scale != 1.0:
            detected = {
                k: [{"x": p["x"] / scale, "y": p["y"] / scale} for p in v]
                for k, v in detected.items()
            }
        result.metadata["detected_pixels"] = detected
        result.metadata["extract_scale"] = scale
        result.metadata["image_size"] = {"width": orig_w, "height": orig_h}

        await self._run_point_audit(image_bytes, result, semantics, plot_regions)
        return result

    async def _run_point_audit(
        self,
        image_bytes: bytes,
        result: ExtractionResult,
        semantics: dict,
        regions: PlotRegions | None,
    ) -> None:
        detected = result.metadata.get("detected_pixels", {})
        if not result.series:
            return
        summary = format_detected_summary(result.series, detected)
        regions_summary = format_regions_summary(regions)
        semantics_summary = format_semantics_summary(semantics)
        try:
            raw = await self.vlm.audit_points(
                image_bytes, summary, regions_summary, semantics_summary
            )
            removals = parse_audit_removals(raw)
        except Exception:
            removals = []

        result.suggested_removals = removals
        if removals:
            n = len(removals)
            result.low_confidence_flags.append(
                f"AI 建议剔除 {n} 个疑似误识别点，请在校正页确认"
            )

    def _prepare_working_image(self, img) -> tuple:
        h, w = img.shape[:2]
        if min(h, w) >= 800:
            return img, 1.0
        up = upscale_if_small(img, min_dim=800)
        scale = up.shape[1] / w
        return up, scale

    def _series_colors_from_semantics(self, semantics: dict) -> list[str] | None:
        colors = semantics.get("series_colors") or {}
        if not isinstance(colors, dict):
            return None
        hexes = [v for v in colors.values() if isinstance(v, str) and v.startswith("#")]
        return hexes or None


def enrich_series_for_api(result: ExtractionResult, calibration: CalibrationConfig) -> dict:
    calibrator = Calibrator(calibration)
    detected_map = result.metadata.get("detected_pixels", {})
    out = result.model_dump(mode="json")
    series_out = []
    for s in result.series:
        pixel_points = [
            {"x": calibrator.data_to_pixel(p.x, p.y).x, "y": calibrator.data_to_pixel(p.x, p.y).y}
            for p in s.points
        ]
        detected_pixel_points = detected_map.get(s.color_hex or "", [])
        err_list = []
        for e in s.errors:
            err_list.append(e.model_dump() if e is not None and hasattr(e, "model_dump") else e)
        series_out.append(
            {
                "name": s.name,
                "color_hex": s.color_hex,
                "points": [{"x": p.x, "y": p.y} for p in s.points],
                "pixel_points": pixel_points,
                "detected_pixel_points": detected_pixel_points,
                "confidence": s.confidence,
                "has_error_bars": s.has_error_bars,
                "errors": err_list,
            }
        )
    out["series"] = series_out
    out["fit_curves"] = result.metadata.get("fit_curves", [])
    if result.regions:
        out["regions"] = result.regions.model_dump(mode="json")
    out["suggested_removals"] = [r.model_dump(mode="json") for r in result.suggested_removals]
    out["chart_metadata"] = {
        "title": result.title,
        "x_label": result.x_label,
        "y_label": result.y_label,
        "x_quantity": result.x_quantity,
        "y_quantity": result.y_quantity,
        "x_unit": result.x_unit,
        "y_unit": result.y_unit,
        "legend": result.legend,
    }
    return out
