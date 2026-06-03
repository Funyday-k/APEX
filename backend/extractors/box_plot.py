import cv2
import numpy as np

from core.schemas import DataSeries, Point
from extractors.base import BaseExtractor
from extractors.plot_mask import build_plot_mask


class BoxPlotExtractor(BaseExtractor):
    def extract(self, img, calibrator, series_colors=None):
        plot_mask = build_plot_mask(img, calibrator)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        binary = cv2.bitwise_and(binary, plot_mask)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if self._is_box(w, h):
                q3 = calibrator.pixel_to_data(x + w / 2, y).y
                q1 = calibrator.pixel_to_data(x + w / 2, y + h).y
                median = self._find_median_line(binary, x, y, w, h, calibrator)
                whisker_hi, whisker_lo = self._find_whiskers(binary, x, y, w, h, calibrator)
                boxes.append(
                    {
                        "x_pixel": x + w / 2,
                        "q1": q1,
                        "q3": q3,
                        "median": median,
                        "whisker_low": whisker_lo,
                        "whisker_high": whisker_hi,
                    }
                )

        boxes.sort(key=lambda b: b["x_pixel"])
        points = []
        for b in boxes:
            xp = b["x_pixel"]
            x_data = calibrator.pixel_to_data(xp, 0).x
            points.extend(
                [
                    Point(x=x_data, y=b["whisker_low"]),
                    Point(x=x_data, y=b["q1"]),
                    Point(x=x_data, y=b["median"]),
                    Point(x=x_data, y=b["q3"]),
                    Point(x=x_data, y=b["whisker_high"]),
                ]
            )
        return [DataSeries(name="boxplot", points=points, confidence=0.8)] if points else []

    def _is_box(self, w, h):
        return 15 < w < 200 and 15 < h < 600

    def _find_median_line(self, binary, x, y, w, h, calibrator):
        region = binary[y : y + h, x : x + w]
        row_sum = region.sum(axis=1)
        median_row = int(np.argmax(row_sum))
        return calibrator.pixel_to_data(x + w / 2, y + median_row).y

    def _find_whiskers(self, binary, x, y, w, h, calibrator):
        cx = x + w // 2
        col = binary[:, cx]
        ys = np.where(col > 0)[0]
        if len(ys) == 0:
            return (
                calibrator.pixel_to_data(cx, y).y,
                calibrator.pixel_to_data(cx, y + h).y,
            )
        hi = calibrator.pixel_to_data(cx, ys.min()).y
        lo = calibrator.pixel_to_data(cx, ys.max()).y
        return hi, lo
