import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import ErrorBar, PointWithError


class ErrorBarDetector:
    def __init__(self, cap_search_width: int = 15, min_bar_length: int = 4):
        self.cap_search_width = cap_search_width
        self.min_bar_length = min_bar_length

    def detect(
        self,
        mask: np.ndarray,
        point_centers: list[tuple],
        calibrator: Calibrator,
        direction: str = "vertical",
    ) -> list[PointWithError]:
        results = []
        for cx, cy in point_centers:
            if direction == "vertical":
                err = self._detect_vertical(mask, cx, cy, calibrator)
            else:
                err = self._detect_horizontal(mask, cx, cy, calibrator)
            data_pt = calibrator.pixel_to_data(cx, cy)
            results.append(PointWithError(x=data_pt.x, y=data_pt.y, error=err))
        return results

    def _detect_vertical(self, mask, cx, cy, calibrator) -> ErrorBar | None:
        cx, cy = int(cx), int(cy)
        upper_y = self._trace_vertical(mask, cx, cy, step=-1)
        lower_y = self._trace_vertical(mask, cx, cy, step=1)
        up_len = abs(cy - upper_y)
        lo_len = abs(lower_y - cy)
        if up_len < self.min_bar_length and lo_len < self.min_bar_length:
            return None
        center_data = calibrator.pixel_to_data(cx, cy)
        upper_data = calibrator.pixel_to_data(cx, upper_y)
        lower_data = calibrator.pixel_to_data(cx, lower_y)
        return ErrorBar(
            y_err_upper=abs(upper_data.y - center_data.y) if up_len >= self.min_bar_length else None,
            y_err_lower=abs(center_data.y - lower_data.y) if lo_len >= self.min_bar_length else None,
        )

    def _detect_horizontal(self, mask, cx, cy, calibrator) -> ErrorBar | None:
        cx, cy = int(cx), int(cy)
        left_x = self._trace_horizontal(mask, cx, cy, step=-1)
        right_x = self._trace_horizontal(mask, cx, cy, step=1)
        left_len = abs(cx - left_x)
        right_len = abs(right_x - cx)
        if left_len < self.min_bar_length and right_len < self.min_bar_length:
            return None
        center_data = calibrator.pixel_to_data(cx, cy)
        left_data = calibrator.pixel_to_data(left_x, cy)
        right_data = calibrator.pixel_to_data(right_x, cy)
        return ErrorBar(
            x_err_left=abs(center_data.x - left_data.x) if left_len >= self.min_bar_length else None,
            x_err_right=abs(right_data.x - center_data.x) if right_len >= self.min_bar_length else None,
        )

    def _trace_vertical(self, mask, cx, cy, step) -> int:
        h, w = mask.shape
        y, gap_count, last_white = cy, 0, cy
        while 0 <= y < h:
            band = mask[y, max(0, cx - 1) : min(w, cx + 2)]
            if np.any(band > 0):
                last_white, gap_count = y, 0
            else:
                gap_count += 1
                if gap_count > 2:
                    break
            y += step
        return last_white

    def _trace_horizontal(self, mask, cx, cy, step) -> int:
        h, w = mask.shape
        x, gap_count, last_white = cx, 0, cx
        while 0 <= x < w:
            band = mask[max(0, cy - 1) : min(h, cy + 2), x]
            if np.any(band > 0):
                last_white, gap_count = x, 0
            else:
                gap_count += 1
                if gap_count > 2:
                    break
            x += step
        return last_white
