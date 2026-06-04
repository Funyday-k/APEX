import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import DataSeries, PlotRegions, Point
from extractors.base import BaseExtractor
from extractors.color_segmentation import segment_by_color
from extractors.error_band import ErrorBandDetector
from extractors.error_bar import ErrorBarDetector
from extractors.line_tracing import trace_mask_to_points
from extractors.markers import detect_markers, is_marker_dominant, mask_without_markers
from extractors.plot_mask import build_plot_mask, plot_x_range
from preprocessing.region_fusion import point_in_regions, regions_for_mask


class LineChartExtractor(BaseExtractor):
    def __init__(self):
        self._last_detected_pixels: dict[str, list[dict]] = {}
        self._last_error_bands: list = []
        self.error_detector = ErrorBarDetector()
        self.band_detector = ErrorBandDetector()

    def extract(
        self,
        img,
        calibrator,
        series_colors=None,
        regions: PlotRegions | None = None,
        **kwargs,
    ):
        min_marker_area = int(kwargs.get("min_marker_area") or 8)
        plot_mask = build_plot_mask(img, calibrator, regions=regions)
        color_masks = segment_by_color(img, plot_mask, given_colors=series_colors)
        x_min, x_max = plot_x_range(calibrator)
        exclude_regions = regions_for_mask(regions)

        series_list = []
        self._last_detected_pixels = {}
        self._last_error_bands = []

        for color_hex, mask in color_masks.items():
            band = self.band_detector.detect_in_mask(
                img, mask, calibrator, x_min, x_max, color_hex
            )
            if band:
                self._last_error_bands.append(band)

            markers = detect_markers(mask, min_area=min_marker_area)
            if exclude_regions:
                markers = [
                    (cx, cy)
                    for cx, cy in markers
                    if not point_in_regions(cx, cy, exclude_regions)
                ]

            if is_marker_dominant(mask, markers):
                points_with_err = self.error_detector.detect(
                    mask, markers, calibrator, direction="vertical"
                )
                has_err = any(p.error is not None for p in points_with_err)
                points = [Point(x=p.x, y=p.y) for p in points_with_err]
                errors = [p.error for p in points_with_err]
                self._last_detected_pixels[color_hex] = [
                    {"x": cx, "y": cy} for cx, cy in markers
                ]
                ds = DataSeries(
                    name=f"series_{color_hex}",
                    color_hex=color_hex,
                    points=sorted(points, key=lambda p: p.x),
                    confidence=self._marker_confidence(markers),
                    has_error_bars=has_err,
                    errors=errors,
                    representation="marker_line",
                    error_band=band,
                )
                if len(ds.points) >= 2:
                    series_list.append(ds)
                continue

            curve_mask = mask_without_markers(mask, markers) if markers else mask
            points = trace_mask_to_points(
                curve_mask, calibrator, x_min, x_max, peak_mode=True
            )
            if len(points) >= 2:
                self._last_detected_pixels[color_hex] = [
                    {
                        "x": calibrator.data_to_pixel(p.x, p.y).x,
                        "y": calibrator.data_to_pixel(p.x, p.y).y,
                    }
                    for p in points
                ]
                series_list.append(
                    DataSeries(
                        name=f"series_{color_hex}",
                        color_hex=color_hex,
                        points=points,
                        confidence=self._estimate_confidence(curve_mask, points, x_min, x_max),
                        representation="continuous",
                        error_band=band,
                    )
                )
        return series_list

    def _marker_confidence(self, centers: list) -> float:
        return float(min(1.0, 0.6 + len(centers) * 0.05))

    def _estimate_confidence(self, mask, points, x_min, x_max) -> float:
        span = max(1, x_max - x_min)
        coverage = len(points) / span
        return float(min(1.0, 0.5 + coverage))
