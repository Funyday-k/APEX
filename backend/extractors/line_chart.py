import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import DataSeries, Point
from extractors.base import BaseExtractor
from extractors.color_segmentation import segment_by_color


class LineChartExtractor(BaseExtractor):
    def extract(self, img, calibrator, series_colors=None):
        plot_mask = self._build_plot_mask(img, calibrator)
        color_masks = segment_by_color(img, plot_mask, given_colors=series_colors)

        series_list = []
        for color_hex, mask in color_masks.items():
            points = self._trace_line(mask, calibrator)
            if len(points) >= 2:
                series_list.append(
                    DataSeries(
                        name=f"series_{color_hex}",
                        color_hex=color_hex,
                        points=points,
                        confidence=self._estimate_confidence(mask, points),
                    )
                )
        return series_list

    def _build_plot_mask(self, img, calibrator: Calibrator) -> np.ndarray:
        h, w = img.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        xt, yt = calibrator.x_transform, calibrator.y_transform
        x0 = int(min(xt.p1, xt.p2))
        x1 = int(max(xt.p1, xt.p2))
        y0 = int(min(yt.p1, yt.p2))
        y1 = int(max(yt.p1, yt.p2))
        pad = 5
        mask[max(0, y0 - pad) : min(h, y1 + pad), max(0, x0 - pad) : min(w, x1 + pad)] = 255
        return mask

    def _trace_line(self, mask: np.ndarray, calibrator: Calibrator) -> list[Point]:
        points = []
        h, w = mask.shape
        for px in range(w):
            ys = np.where(mask[:, px] > 0)[0]
            if len(ys) == 0:
                continue
            py = self._robust_y(ys)
            points.append(calibrator.pixel_to_data(px, py))
        return self._smooth(points)

    def _robust_y(self, ys: np.ndarray) -> float:
        if len(ys) <= 3:
            return float(np.median(ys))
        gaps = np.where(np.diff(ys) > 3)[0]
        segments = np.split(ys, gaps + 1)
        largest = max(segments, key=len)
        return float(np.median(largest))

    def _smooth(self, points: list[Point], window=3) -> list[Point]:
        if len(points) < window:
            return points
        ys = np.array([p.y for p in points])
        half = window // 2
        ys_smooth = ys.copy()
        for i in range(len(ys)):
            lo = max(0, i - half)
            hi = min(len(ys), i + half + 1)
            ys_smooth[i] = np.median(ys[lo:hi])
        return [Point(x=p.x, y=float(ys_smooth[i])) for i, p in enumerate(points)]

    def _estimate_confidence(self, mask, points) -> float:
        coverage = len(points) / max(1, mask.shape[1])
        return float(min(1.0, 0.5 + coverage))
