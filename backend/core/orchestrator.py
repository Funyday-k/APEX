from calibration.axis_detector import detect_axes
from calibration.calibrator import Calibrator
from calibration.tick_detector import detect_ticks
from classification.classifier import classify_chart
from core.schemas import CalibrationConfig, ChartType, ExtractionResult, HeatmapOptions
from extractors import get_extractor
from ocr.ocr_engine import OCREngine
from preprocessing.enhance import enhance
from preprocessing.loader import load_image
from preprocessing.plot_area import detect_plot_area
from validation.cross_validator import CrossValidator
from vlm.provider import get_vlm_provider


class Orchestrator:
    def __init__(self):
        self.ocr = OCREngine()
        self.vlm = get_vlm_provider()
        self.validator = CrossValidator()

    async def auto_analyze(self, image_bytes: bytes) -> dict:
        img = load_image(image_bytes)
        img = enhance(img)

        plot_area = detect_plot_area(img)
        chart_type = await classify_chart(img, self.vlm)
        ocr_results = self.ocr.extract(img)
        semantics = await self.vlm.analyze_semantics(image_bytes)
        axes = detect_axes(img, plot_area)
        ticks = detect_ticks(img, axes, ocr_results)

        return {
            "chart_type": chart_type.value if hasattr(chart_type, "value") else chart_type,
            "plot_area": plot_area,
            "ocr": ocr_results,
            "semantics": semantics,
            "suggested_calibration": ticks,
        }

    async def extract(
        self,
        image_bytes: bytes,
        chart_type: ChartType,
        calibration: CalibrationConfig,
        series_colors: list[str] | None = None,
        heatmap_options: HeatmapOptions | None = None,
    ) -> ExtractionResult:
        img = load_image(image_bytes)
        img = enhance(img)

        extractor = get_extractor(chart_type)
        calibrator = Calibrator(calibration)

        if chart_type == ChartType.HEATMAP:
            cv_series = extractor.extract(
                img, calibrator, series_colors, heatmap_options=heatmap_options
            )
        else:
            cv_series = extractor.extract(img, calibrator, series_colors)

        semantics = await self.vlm.analyze_semantics(image_bytes)
        semantics["chart_type"] = chart_type.value

        result = self.validator.validate(cv_series, semantics, img)
        result.chart_type = chart_type

        fit_curves = getattr(extractor, "_last_fit_curves", [])
        if fit_curves:
            result.metadata["fit_curves"] = [
                f.model_dump(mode="json") if hasattr(f, "model_dump") else f for f in fit_curves
            ]

        calibrator = Calibrator(calibration)
        result.metadata["pixel_mapping"] = True
        return result


def enrich_series_for_api(result: ExtractionResult, calibration: CalibrationConfig) -> dict:
    calibrator = Calibrator(calibration)
    out = result.model_dump(mode="json")
    series_out = []
    for s in result.series:
        pixel_points = [
            {"x": calibrator.data_to_pixel(p.x, p.y).x, "y": calibrator.data_to_pixel(p.x, p.y).y}
            for p in s.points
        ]
        err_list = []
        for e in s.errors:
            err_list.append(e.model_dump() if e is not None and hasattr(e, "model_dump") else e)
        series_out.append(
            {
                "name": s.name,
                "color_hex": s.color_hex,
                "points": [{"x": p.x, "y": p.y} for p in s.points],
                "pixel_points": pixel_points,
                "confidence": s.confidence,
                "has_error_bars": s.has_error_bars,
                "errors": err_list,
            }
        )
    out["series"] = series_out
    out["fit_curves"] = result.metadata.get("fit_curves", [])
    return out
