import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import FitCurve, Point


class FitCurveAnalyzer:
    SMOOTHNESS_THRESHOLD = 0.05
    CONTINUITY_THRESHOLD = 0.85

    def is_fit_curve(self, mask: np.ndarray) -> bool:
        continuity = self._continuity_ratio(mask)
        if continuity < self.CONTINUITY_THRESHOLD:
            return False
        smoothness = self._smoothness(mask)
        marker_score = self._marker_likelihood(mask)
        return smoothness < self.SMOOTHNESS_THRESHOLD and marker_score < 0.3

    def _continuity_ratio(self, mask: np.ndarray) -> float:
        xs = np.where(np.any(mask > 0, axis=0))[0]
        if len(xs) < 2:
            return 0.0
        cols_with_data = len(xs)
        span = xs.max() - xs.min() + 1
        return cols_with_data / span

    def _smoothness(self, mask: np.ndarray) -> float:
        ys = self._extract_curve_y(mask)
        if len(ys) < 3:
            return 1.0
        ys = np.array(ys, dtype=float)
        second_diff = np.abs(np.diff(ys, 2))
        norm = np.std(ys) + 1e-9
        return float(np.mean(second_diff) / norm)

    def _extract_curve_y(self, mask: np.ndarray) -> list[float]:
        ys = []
        h, w = mask.shape
        for px in range(w):
            col = np.where(mask[:, px] > 0)[0]
            if len(col) > 0:
                ys.append(float(np.median(col)))
        return ys

    def _marker_likelihood(self, mask: np.ndarray) -> float:
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if n <= 1:
            return 0.0
        marker_count = 0
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            w_ = stats[i, cv2.CC_STAT_WIDTH]
            h_ = stats[i, cv2.CC_STAT_HEIGHT]
            if 10 <= area <= 400 and 0.5 <= w_ / max(h_, 1) <= 2.0:
                marker_count += 1
        return min(1.0, marker_count / 10.0)

    def extract_fit_curve(
        self, mask: np.ndarray, calibrator: Calibrator, color_hex: str
    ) -> FitCurve:
        ys_px = self._extract_curve_y(mask)
        xs_px = [px for px in range(mask.shape[1]) if np.any(mask[:, px] > 0)]
        points = []
        for px, py in zip(xs_px, ys_px):
            dp = calibrator.pixel_to_data(px, py)
            points.append(Point(x=dp.x, y=dp.y))
        curve_type = self._identify_function(points)
        return FitCurve(
            name=f"fit_{color_hex}",
            color_hex=color_hex,
            points=points,
            curve_type=curve_type,
            is_fit=True,
        )

    def _identify_function(self, points: list[Point]) -> str:
        if len(points) < 5:
            return "unknown"
        x = np.array([p.x for p in points])
        y = np.array([p.y for p in points])
        try:
            from scipy.optimize import curve_fit
        except ImportError:
            return "unknown"

        def linear(xv, a, b):
            return a * xv + b

        candidates = {
            "linear": (linear, 2),
            "quadratic": (lambda xv, a, b, c: a * xv**2 + b * xv + c, 3),
        }
        best_type, best_r2 = "unknown", -np.inf
        for name, (func, _) in candidates.items():
            try:
                popt, _ = curve_fit(func, x, y, maxfev=5000)
                y_pred = func(x, *popt)
                r2 = self._r_squared(y, y_pred)
                if r2 > best_r2:
                    best_r2, best_type = r2, name
            except Exception:
                continue
        return best_type if best_r2 > 0.9 else "unknown"

    @staticmethod
    def _r_squared(y, y_pred) -> float:
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2) + 1e-12
        return 1.0 - ss_res / ss_tot
