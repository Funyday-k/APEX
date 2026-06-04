from calibration.auto_calibrate import ticks_to_calibration_config
from calibration.axis_detector import detect_axes
from calibration.calibrator import Calibrator
from calibration.tick_detector import build_tick_label_regions, detect_ticks
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
from extractors.cases import (
    build_cases,
    build_extraction_result,
    extract_cases_on_image,
)
from ocr.ocr_engine import OCREngine
from preprocessing.enhance import enhance, upscale_if_small
from preprocessing.loader import load_image
from calibration.scale_detector import infer_axis_scales
from preprocessing.plot_area import constrain_plot_area_with_axes, detect_plot_area
from preprocessing.region_fusion import (
    axis_confidence_from_geometry,
    chart_metadata_from_semantics,
    merge_axis_regions,
    merge_plot_area,
    merge_tick_label_regions,
    parse_vlm_regions,
)
from preprocessing.vlm_image import prepare_vlm_image
from preprocessing.legend_detector import detect_legend_regions, merge_legend_regions
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

    async def auto_analyze(
        self,
        image_bytes: bytes,
        *,
        chart_type_override: str | None = None,
        use_vlm_regions: bool = True,
        force_redetect_plot: bool = False,
    ) -> dict:
        vlm_bytes, img, w, h = prepare_vlm_image(image_bytes)

        # Preliminary axes on rough plot area for tick-guided boundary
        rough_plot = detect_plot_area(img)
        rough_axes = detect_axes(img, rough_plot)
        ocr_results = self.ocr.extract(img)
        pre_ticks = detect_ticks(img, rough_axes, ocr_results)
        x_tick_px = [int(t["pixel"]) for t in pre_ticks.get("x_ticks", [])]

        plot_area = detect_plot_area(img, x_tick_pixels=x_tick_px or None)
        if force_redetect_plot:
            plot_area["detected"] = True

        axes_pre = detect_axes(img, plot_area)
        plot_area = constrain_plot_area_with_axes(plot_area, axes_pre, w, h)

        chart_type = await classify_chart(img, self.vlm)
        if chart_type_override:
            try:
                chart_type = ChartType(chart_type_override)
            except ValueError:
                pass

        semantics = await self.vlm.analyze_semantics(vlm_bytes)

        regions_raw = {}
        if use_vlm_regions:
            regions_raw = await self.vlm.segment_regions(vlm_bytes)
        regions = parse_vlm_regions(regions_raw, w, h) if regions_raw else PlotRegions(
            image_width=w, image_height=h, source="none"
        )
        regions = merge_plot_area(regions, plot_area, w, h)

        axes = detect_axes(img, plot_area)
        plot_area = constrain_plot_area_with_axes(plot_area, axes, w, h)
        regions = merge_plot_area(regions, plot_area, w, h)
        regions = merge_axis_regions(regions, axes, w, h)
        tick_regions = build_tick_label_regions(ocr_results, axes, w, h)
        regions = merge_tick_label_regions(regions, tick_regions)

        cv_legends = detect_legend_regions(img, plot_area, ocr_results, w, h)
        regions = merge_legend_regions(regions, cv_legends, w, h)

        ticks = detect_ticks(img, axes, ocr_results)
        chart_metadata = chart_metadata_from_semantics(semantics)
        axis_confidence = axis_confidence_from_geometry(axes, plot_area)

        scale_info = infer_axis_scales(
            ticks,
            x_label=semantics.get("x_label") or chart_metadata.get("x_label"),
            y_label=semantics.get("y_label") or chart_metadata.get("y_label"),
            vlm_x_scale=semantics.get("x_scale") or chart_metadata.get("x_scale"),
            vlm_y_scale=semantics.get("y_scale") or chart_metadata.get("y_scale"),
        )
        x_scale = scale_info["x_scale"]
        y_scale = scale_info["y_scale"]
        chart_metadata["x_scale"] = x_scale
        chart_metadata["y_scale"] = y_scale
        suggested_config = ticks_to_calibration_config(ticks, axes, x_scale, y_scale)
        auto_applied = False
        auto_threshold = 0.65
        if suggested_config and suggested_config.get("auto_confidence", 0) >= auto_threshold:
            auto_applied = True

        ocr_summary = [
            item.get("text", "")
            for item in ocr_results
            if item.get("text")
        ][:40]

        vlm_cases_raw = await self.vlm.detect_cases(vlm_bytes)
        cases = build_cases(semantics, vlm_cases_raw, w, h)

        return {
            "chart_type": chart_type.value if hasattr(chart_type, "value") else chart_type,
            "plot_area": plot_area,
            "ocr": ocr_results,
            "semantics": semantics,
            "suggested_calibration": ticks,
            "suggested_calibration_config": (
                {
                    k: v
                    for k, v in suggested_config.items()
                    if k not in ("auto_confidence", "calibration_diagnostics")
                }
                if suggested_config
                else None
            ),
            "auto_calibration_applied": auto_applied,
            "auto_calibration_confidence": (
                suggested_config.get("auto_confidence", 0) if suggested_config else 0
            ),
            "calibration_diagnostics": (
                suggested_config.get("calibration_diagnostics") if suggested_config else None
            ),
            "axis_geometry": axes,
            "axis_confidence": axis_confidence,
            "scale_detection": scale_info,
            "regions": regions.model_dump(mode="json"),
            "chart_metadata": chart_metadata,
            "analysis_snapshot": {
                "ocr_summary": ocr_summary,
                "plot_area": plot_area,
                "image_width": w,
                "image_height": h,
            },
            "cases": cases,
        }

    async def extract_cases(
        self,
        image_bytes: bytes,
        cases: list[dict],
        calibration: CalibrationConfig,
        semantics: dict | None = None,
        regions: dict | PlotRegions | None = None,
        extract_options: dict | None = None,
    ) -> ExtractionResult:
        extract_options = extract_options or {}
        img = load_image(image_bytes)
        img = enhance(img)
        img_work, scale = self._prepare_working_image(img)
        cal_work = scale_calibration(calibration, scale) if scale != 1.0 else calibration
        calibrator = Calibrator(cal_work)
        orig_h, orig_w = img.shape[:2]
        plot_regions = _parse_regions_payload(regions, orig_w, orig_h)
        if plot_regions and scale != 1.0:
            plot_regions = _scale_regions(plot_regions, scale)

        series = extract_cases_on_image(
            img_work,
            calibrator,
            cases,
            plot_regions=plot_regions,
            extract_options=extract_options,
        )
        if semantics is None:
            vlm_bytes, _, _, _ = prepare_vlm_image(image_bytes)
            semantics = await self.vlm.analyze_semantics(vlm_bytes)

        result = build_extraction_result(series, semantics, ChartType.SCATTER)
        result.regions = plot_regions
        if extract_options.get("enable_vlm_audit", True):
            await self._run_point_audit(image_bytes, result, semantics or {}, plot_regions)
        return result

    async def extract(
        self,
        image_bytes: bytes,
        chart_type: ChartType,
        calibration: CalibrationConfig,
        series_colors: list[str] | None = None,
        heatmap_options: HeatmapOptions | None = None,
        semantics: dict | None = None,
        regions: dict | PlotRegions | None = None,
        extract_options: dict | None = None,
    ) -> ExtractionResult:
        extract_options = extract_options or {}
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

        extract_kw = {"regions": plot_regions, **extract_options}
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
            vlm_bytes, _, _, _ = prepare_vlm_image(image_bytes)
            semantics = await self.vlm.analyze_semantics(vlm_bytes)
        semantics = dict(semantics)
        semantics["chart_type"] = chart_type.value

        if plot_regions is None:
            h_work, w_work = img_work.shape[:2]
            vlm_bytes, _, _, _ = prepare_vlm_image(image_bytes)
            regions_raw = await self.vlm.segment_regions(vlm_bytes)
            if regions_raw:
                pr = parse_vlm_regions(regions_raw, orig_w, orig_h)
                plot_regions = _scale_regions(pr, scale) if scale != 1.0 else pr
                plot_regions.image_width = w_work
                plot_regions.image_height = h_work

        result = self.validator.validate(cv_series, semantics, img_work)
        result.chart_type = chart_type
        result.regions = plot_regions

        if extract_options.get("enable_ai_evaluation", True):
            eval_flags, eval_score = await self._evaluate_extraction(
                image_bytes, result, semantics, plot_regions
            )
            if eval_flags:
                result.low_confidence_flags.extend(eval_flags)
            if eval_score is not None:
                result.overall_confidence = float(
                    0.65 * result.overall_confidence + 0.35 * eval_score
                )
            result.metadata["ai_evaluation_score"] = eval_score

        fit_curves = getattr(extractor, "_last_fit_curves", [])
        if fit_curves:
            result.metadata["fit_curves"] = [
                f.model_dump(mode="json") if hasattr(f, "model_dump") else f for f in fit_curves
            ]

        error_bands = getattr(extractor, "_last_error_bands", [])
        if error_bands:
            result.metadata["error_bands"] = [
                b.model_dump(mode="json") if hasattr(b, "model_dump") else b for b in error_bands
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

        if extract_options.get("enable_vlm_audit", True):
            await self._run_point_audit(image_bytes, result, semantics, plot_regions)
        return result

    async def _evaluate_extraction(
        self,
        image_bytes: bytes,
        result: ExtractionResult,
        semantics: dict,
        regions: PlotRegions | None,
    ) -> tuple[list[str], float | None]:
        flags: list[str] = []
        score: float | None = None
        try:
            summary = format_detected_summary(result.series, result.metadata.get("detected_pixels", {}))
            regions_summary = format_regions_summary(regions)
            semantics_summary = format_semantics_summary(semantics)
            raw = await self.vlm.evaluate_extraction(
                image_bytes, summary, regions_summary, semantics_summary
            )
            if raw:
                score = float(raw.get("overall_score", 0)) if raw.get("overall_score") is not None else None
                for issue in raw.get("issues", []) or []:
                    if isinstance(issue, str) and issue:
                        flags.append(issue)
                if raw.get("plot_area_incomplete"):
                    flags.append("AI: 绘图区右边界可能不完整，建议重新分析或手动调整区域")
                if raw.get("calibration_suspect"):
                    flags.append("AI: 坐标标定可能不准确，请检查对数轴与刻度值")
        except Exception:
            pass

        # Heuristic: plot_area vs data extent
        if regions:
            pa = next((r for r in regions.regions if r.kind == "plot_area"), None)
            if pa and result.series:
                max_px = max(
                    (p.x for s in result.series for p in (s.points or [])),
                    default=0,
                )
                # pixel extent check uses metadata detected pixels if available
                det = result.metadata.get("detected_pixels", {})
                all_det_x = [
                    p["x"]
                    for pts in det.values()
                    for p in pts
                    if isinstance(p, dict) and "x" in p
                ]
                if all_det_x and max(all_det_x) > pa.bbox.x1 * 0.98:
                    flags.append("检测点接近绘图区右缘，绘图区可能偏窄")

        return flags, score

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
                "representation": s.representation,
                "error_band": (
                    s.error_band.model_dump(mode="json") if s.error_band else None
                ),
            }
        )
    out["series"] = series_out
    out["fit_curves"] = result.metadata.get("fit_curves", [])
    out["error_bands"] = result.metadata.get("error_bands", [])
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
