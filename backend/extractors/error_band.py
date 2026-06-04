"""Detect shaded uncertainty / confidence bands in line charts."""

from __future__ import annotations

import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import Point, UncertaintyBand
from extractors.line_tracing import trace_mask_to_points


class ErrorBandDetector:
    """Extract upper/lower envelope from low-saturation filled regions."""

    def detect_in_mask(
        self,
        img: np.ndarray,
        color_mask: np.ndarray,
        calibrator: Calibrator,
        x_min: int,
        x_max: int,
        color_hex: str,
        name: str | None = None,
    ) -> UncertaintyBand | None:
        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        sat = hsv[:, :, 1].astype(float)
        # Band fill is often desaturated relative to line stroke
        band_mask = ((color_mask > 0) & (sat < 120)).astype(np.uint8) * 255
        if cv2.countNonZero(band_mask) < 100:
            return None

        upper_mask = self._upper_envelope_mask(band_mask)
        lower_mask = self._lower_envelope_mask(band_mask)
        if cv2.countNonZero(upper_mask) < 20 or cv2.countNonZero(lower_mask) < 20:
            return None

        upper_pts = trace_mask_to_points(upper_mask, calibrator, x_min, x_max, peak_mode=True)
        lower_pts = trace_mask_to_points(lower_mask, calibrator, x_min, x_max, peak_mode=False)
        if len(upper_pts) < 3 or len(lower_pts) < 3:
            return None

        return UncertaintyBand(
            name=name or f"band_{color_hex}",
            color_hex=color_hex,
            upper_points=upper_pts,
            lower_points=lower_pts,
        )

    def _upper_envelope_mask(self, mask: np.ndarray) -> np.ndarray:
        h, w = mask.shape
        out = np.zeros_like(mask)
        for x in range(w):
            ys = np.where(mask[:, x] > 0)[0]
            if len(ys) >= 2:
                y_top = int(np.min(ys))
                out[max(0, y_top - 1) : y_top + 2, x] = 255
            elif len(ys) == 1:
                out[ys[0], x] = 255
        return out

    def _lower_envelope_mask(self, mask: np.ndarray) -> np.ndarray:
        h, w = mask.shape
        out = np.zeros_like(mask)
        for x in range(w):
            ys = np.where(mask[:, x] > 0)[0]
            if len(ys) >= 2:
                y_bot = int(np.max(ys))
                out[max(0, y_bot - 1) : min(h, y_bot + 2), x] = 255
            elif len(ys) == 1:
                out[ys[0], x] = 255
        return out
