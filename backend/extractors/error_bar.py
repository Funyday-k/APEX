import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import ErrorBar, PointWithError


class ErrorBarDetector:
    def __init__(self, cap_search_width: int = 15, min_bar_length: int = 4, cap_min_len: int = 3):
        self.cap_search_width = cap_search_width
        self.min_bar_length = min_bar_length
        self.cap_min_len = cap_min_len

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
            elif direction == "horizontal":
                err = self._detect_horizontal(mask, cx, cy, calibrator)
            else:
                v_err = self._detect_vertical(mask, cx, cy, calibrator)
                h_err = self._detect_horizontal(mask, cx, cy, calibrator)
                err = self._merge_errors(v_err, h_err)
            data_pt = calibrator.pixel_to_data(cx, cy)
            results.append(PointWithError(x=data_pt.x, y=data_pt.y, error=err))
        return results

    def _merge_errors(self, v: ErrorBar | None, h: ErrorBar | None) -> ErrorBar | None:
        if v is None and h is None:
            return None
        return ErrorBar(
            y_err_upper=v.y_err_upper if v else None,
            y_err_lower=v.y_err_lower if v else None,
            x_err_left=h.x_err_left if h else None,
            x_err_right=h.x_err_right if h else None,
        )

    def _detect_vertical(self, mask, cx, cy, calibrator) -> ErrorBar | None:
        cx, cy = int(cx), int(cy)
        upper_y = self._trace_vertical(mask, cx, cy, step=-1)
        lower_y = self._trace_vertical(mask, cx, cy, step=1)
        up_len = abs(cy - upper_y)
        lo_len = abs(lower_y - cy)
        if up_len < self.min_bar_length and lo_len < self.min_bar_length:
            return None
        has_cap_up = self._has_horizontal_cap(mask, upper_y, cx, step=-1) or self._has_horizontal_cap(
            mask, upper_y, cx, step=1
        )
        has_cap_lo = self._has_horizontal_cap(mask, lower_y, cx, step=-1) or self._has_horizontal_cap(
            mask, lower_y, cx, step=1
        )
        center_data = calibrator.pixel_to_data(cx, cy)
        upper_data = calibrator.pixel_to_data(cx, upper_y)
        lower_data = calibrator.pixel_to_data(cx, lower_y)
        y_up = abs(upper_data.y - center_data.y) if up_len >= self.min_bar_length else None
        y_lo = abs(center_data.y - lower_data.y) if lo_len >= self.min_bar_length else None
        if not has_cap_up and not has_cap_lo and y_up is None and y_lo is None:
            return None
        return ErrorBar(y_err_upper=y_up, y_err_lower=y_lo)

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

    def _has_horizontal_cap(self, mask, y, cx, step: int) -> bool:
        h, w = mask.shape
        y = int(y)
        length = 0
        x = int(cx)
        while 0 <= x < w and 0 <= y < h:
            if mask[y, x] > 0:
                length += 1
                if length >= self.cap_min_len:
                    return True
            else:
                if length > 0:
                    break
            x += step
        return length >= self.cap_min_len

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
