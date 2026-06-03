import cv2
import numpy as np

from core.schemas import DataSeries, Point
from extractors.base import BaseExtractor
from extractors.color_segmentation import segment_by_color
from extractors.error_bar import ErrorBarDetector
from extractors.fit_curve import FitCurveAnalyzer
from extractors.line_chart import LineChartExtractor


class ScatterExtractor(BaseExtractor):
    def __init__(self):
        self.error_detector = ErrorBarDetector()
        self.fit_analyzer = FitCurveAnalyzer()
        self._last_fit_curves = []
        self._last_point_errors = []

    def extract(self, img, calibrator, series_colors=None, **kwargs):
        plot_mask = LineChartExtractor()._build_plot_mask(img, calibrator)
        color_masks = segment_by_color(img, plot_mask, given_colors=series_colors)

        data_series = []
        fit_curves = []
        all_errors = []

        for color_hex, mask in color_masks.items():
            if self.fit_analyzer.is_fit_curve(mask):
                fit_curves.append(
                    self.fit_analyzer.extract_fit_curve(mask, calibrator, color_hex)
                )
                continue

            centers = self._detect_points(mask)
            if not centers:
                continue

            points_with_err = self.error_detector.detect(
                mask, centers, calibrator, direction="vertical"
            )
            has_err = any(p.error is not None for p in points_with_err)
            points = [Point(x=p.x, y=p.y) for p in points_with_err]
            errors = [p.error for p in points_with_err]
            all_errors.append(errors)

            data_series.append(
                DataSeries(
                    name=f"series_{color_hex}",
                    color_hex=color_hex,
                    points=points,
                    confidence=0.9,
                    has_error_bars=has_err,
                    errors=errors,
                )
            )

        self._last_fit_curves = fit_curves
        self._last_point_errors = all_errors
        return data_series

    def _detect_points(self, mask: np.ndarray) -> list[tuple]:
        n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        centers = []
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            w_ = stats[i, cv2.CC_STAT_WIDTH]
            h_ = stats[i, cv2.CC_STAT_HEIGHT]
            aspect = w_ / max(h_, 1)
            if 5 <= area <= 800 and 0.3 <= aspect <= 3.0:
                cx, cy = centroids[i]
                centers.append((float(cx), float(cy)))
        return centers
