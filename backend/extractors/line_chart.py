import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import DataSeries, PlotRegions, Point
from extractors.base import BaseExtractor
from extractors.color_segmentation import segment_by_color
from extractors.line_tracing import trace_mask_to_points
from extractors.plot_mask import build_plot_mask, plot_x_range


class LineChartExtractor(BaseExtractor):
    def __init__(self):
        self._last_detected_pixels: dict[str, list[dict]] = {}

    def extract(self, img, calibrator, series_colors=None, regions: PlotRegions | None = None, **kwargs):
        plot_mask = build_plot_mask(img, calibrator, regions=regions)
        color_masks = segment_by_color(img, plot_mask, given_colors=series_colors)
        x_min, x_max = plot_x_range(calibrator)

        series_list = []
        self._last_detected_pixels = {}

        for color_hex, mask in color_masks.items():
            points = trace_mask_to_points(mask, calibrator, x_min, x_max, peak_mode=True)
            if len(points) >= 2:
                self._last_detected_pixels[color_hex] = [
                    {"x": calibrator.data_to_pixel(p.x, p.y).x, "y": calibrator.data_to_pixel(p.x, p.y).y}
                    for p in points
                ]
                series_list.append(
                    DataSeries(
                        name=f"series_{color_hex}",
                        color_hex=color_hex,
                        points=points,
                        confidence=self._estimate_confidence(mask, points, x_min, x_max),
                    )
                )
        return series_list

    def _estimate_confidence(self, mask, points, x_min, x_max) -> float:
        span = max(1, x_max - x_min)
        coverage = len(points) / span
        return float(min(1.0, 0.5 + coverage))
