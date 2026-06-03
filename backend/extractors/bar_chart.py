import cv2
import numpy as np

from core.schemas import DataSeries, Point
from extractors.base import BaseExtractor


class BarChartExtractor(BaseExtractor):
    def extract(self, img, calibrator, series_colors=None):
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bars = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if self._is_bar(w, h, c):
                top_px = x + w / 2
                top_py = y
                data_top = calibrator.pixel_to_data(top_px, top_py)
                bars.append((top_px, data_top))

        bars.sort(key=lambda b: b[0])
        points = [b[1] for b in bars]
        return [DataSeries(name="bars", points=points, confidence=0.9)] if points else []

    def _is_bar(self, w, h, contour) -> bool:
        area = cv2.contourArea(contour)
        rect_area = w * h
        return rect_area > 200 and area / rect_area > 0.8 and h > w * 0.3
