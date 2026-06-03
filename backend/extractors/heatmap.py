import numpy as np

from core.schemas import DataSeries, HeatmapOptions, Point
from extractors.base import BaseExtractor
from extractors.line_chart import LineChartExtractor


class HeatmapExtractor(BaseExtractor):
    def extract(self, img, calibrator, series_colors=None, heatmap_options: HeatmapOptions | None = None):
        if heatmap_options is None:
            raise ValueError("热图需提供 heatmap_options（colorbar_box, value_range）")
        lut = self._build_colorbar_lut(
            img, heatmap_options.colorbar_box, heatmap_options.value_range
        )
        matrix = self._sample_grid(img, calibrator, lut, heatmap_options.grid)
        points = []
        rows, cols = matrix.shape
        for r in range(rows):
            for c in range(cols):
                points.append(Point(x=float(c), y=float(matrix[r, c])))
        return [DataSeries(name="heatmap", points=points, confidence=0.85)]

    def _build_colorbar_lut(self, img, box: dict, value_range: tuple):
        x0, y0 = box["x0"], box["y0"]
        x1, y1 = box["x1"], box["y1"]
        vmin, vmax = value_range
        vertical = (y1 - y0) > (x1 - x0)
        samples = []
        if vertical:
            for py in range(y0, y1):
                color = img[py, (x0 + x1) // 2].astype(float)
                t = (py - y0) / max(y1 - y0, 1)
                value = vmax - t * (vmax - vmin)
                samples.append((color, value))
        else:
            for px in range(x0, x1):
                color = img[(y0 + y1) // 2, px].astype(float)
                t = (px - x0) / max(x1 - x0, 1)
                value = vmin + t * (vmax - vmin)
                samples.append((color, value))
        return samples

    def _color_to_value(self, color, lut):
        best_v, best_d = None, 1e9
        for c, v in lut:
            d = np.linalg.norm(color - c)
            if d < best_d:
                best_d, best_v = d, v
        return best_v

    def _sample_grid(self, img, calibrator, lut, grid):
        plot_mask = LineChartExtractor()._build_plot_mask(img, calibrator)
        xt, yt = calibrator.x_transform, calibrator.y_transform
        x0, x1 = int(min(xt.p1, xt.p2)), int(max(xt.p1, xt.p2))
        y0, y1 = int(min(yt.p1, yt.p2)), int(max(yt.p1, yt.p2))
        rows, cols = grid
        matrix = np.zeros((rows, cols))
        cell_w = (x1 - x0) / cols
        cell_h = (y1 - y0) / rows
        for r in range(rows):
            for c in range(cols):
                cx = int(x0 + (c + 0.5) * cell_w)
                cy = int(y0 + (r + 0.5) * cell_h)
                if 0 <= cy < img.shape[0] and 0 <= cx < img.shape[1]:
                    color = img[cy, cx].astype(float)
                    matrix[r, c] = self._color_to_value(color, lut) or 0.0
        return matrix
