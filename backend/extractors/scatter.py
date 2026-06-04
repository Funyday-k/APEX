import cv2
import numpy as np

from core.schemas import DataSeries, PlotRegions, Point
from preprocessing.region_fusion import point_in_regions, regions_for_mask
from extractors.base import BaseExtractor
from extractors.color_segmentation import segment_by_color
from extractors.error_bar import ErrorBarDetector
from extractors.fit_curve import FitCurveAnalyzer
from extractors.line_tracing import trace_mask_to_points
from extractors.markers import detect_markers, mask_without_markers
from extractors.plot_mask import build_plot_mask, plot_x_range


class ScatterExtractor(BaseExtractor):
    def __init__(self):
        self.error_detector = ErrorBarDetector()
        self.fit_analyzer = FitCurveAnalyzer()
        self._last_fit_curves = []
        self._last_point_errors = []
        self._last_detected_pixels: dict[str, list[dict]] = {}

    def extract(self, img, calibrator, series_colors=None, regions: PlotRegions | None = None, **kwargs):
        min_marker_area = int(kwargs.get("min_marker_area") or 8)
        plot_mask = build_plot_mask(img, calibrator, regions=regions)
        exclude_regions = regions_for_mask(regions)
        color_masks = segment_by_color(img, plot_mask, given_colors=series_colors)
        x_min, x_max = plot_x_range(calibrator)

        data_series = []
        fit_curves = []
        self._last_detected_pixels = {}

        for color_hex, mask in color_masks.items():
            marker_centers = detect_markers(mask, min_area=min_marker_area)
            if exclude_regions:
                marker_centers = [
                    (cx, cy)
                    for cx, cy in marker_centers
                    if not point_in_regions(cx, cy, exclude_regions)
                ]
            curve_mask = mask_without_markers(mask, marker_centers)

            if marker_centers:
                points_with_err = self.error_detector.detect(
                    mask, marker_centers, calibrator, direction="vertical"
                )
                has_err = any(p.error is not None for p in points_with_err)
                points = [Point(x=p.x, y=p.y) for p in points_with_err]
                errors = [p.error for p in points_with_err]
                self._last_detected_pixels[color_hex] = [
                    {"x": cx, "y": cy} for cx, cy in marker_centers
                ]
                data_series.append(
                    DataSeries(
                        name=f"series_{color_hex}",
                        color_hex=color_hex,
                        points=points,
                        confidence=self._marker_confidence(marker_centers),
                        has_error_bars=has_err,
                        errors=errors,
                        representation="markers",
                    )
                )

            if self.fit_analyzer.is_fit_curve(curve_mask):
                fit_curves.append(
                    self.fit_analyzer.extract_fit_curve(curve_mask, calibrator, color_hex)
                )
            elif not marker_centers and cv2.countNonZero(curve_mask) > 50:
                line_pts = trace_mask_to_points(curve_mask, calibrator, x_min, x_max)
                if len(line_pts) >= 2:
                    fit_curves.append(
                        self.fit_analyzer.extract_fit_curve(curve_mask, calibrator, color_hex)
                    )

        self._last_fit_curves = fit_curves
        return data_series

    def _marker_confidence(self, centers: list) -> float:
        return float(min(1.0, 0.6 + len(centers) * 0.05))
