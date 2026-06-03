# 附录 A：误差棒与拟合曲线检测

> 分册说明：进阶模块 A。前置阅读 [core/01-framework.md](../core/01-framework.md) §8。

---

## 目录

1. [模块 A：误差棒 / 拟合曲线检测](#模块-a误差棒--拟合曲线检测)
2. [模块 B：本地 VLM 部署（GPU/CPU + 量化）](#模块-b本地-vlm-部署)
3. [模块 C：前端完整页面与交互流程](#模块-c前端完整页面与交互流程)

---

# 模块 A：误差棒 / 拟合曲线检测

科研图中，**误差棒（error bar）**和**拟合曲线（fit curve）**是关键信息，但与普通数据点混在一起，需要专门算法分离。

## A.1 整体策略

```
原始数据系列（散点/折线）
      │
      ├──→ 误差棒检测：寻找数据点上下/左右的"T形"竖线
      │         └─→ 计算每个点的 y_err（或 x_err）
      │
      └──→ 拟合曲线检测：区分"平滑连续曲线"与"离散数据点"
                └─→ 平滑度+连续性判据，标记为 fit 而非 data
```

**关键区分原则**：

| 特征 | 数据点 | 拟合曲线 | 误差棒 |
|------|--------|----------|--------|
| 形状 | 离散标记（圆/方/三角） | 连续平滑线 | 细竖线+顶帽 |
| 连续性 | 不连续 | 高度连续 | 垂直短线段 |
| 平滑度 | — | 二阶差分小 | — |
| 位置 | 独立 | 贯穿全图 | 锚定在数据点 |

## A.2 数据结构扩展 `core/schemas.py`（新增）

```python
from pydantic import BaseModel
from typing import Optional


class ErrorBar(BaseModel):
    """单个数据点的误差信息"""
    y_err_upper: Optional[float] = None
    y_err_lower: Optional[float] = None
    x_err_left: Optional[float] = None
    x_err_right: Optional[float] = None


class PointWithError(BaseModel):
    x: float
    y: float
    error: Optional[ErrorBar] = None


class FitCurve(BaseModel):
    """拟合曲线（与离散数据点区分）"""
    name: str
    color_hex: Optional[str] = None
    points: list  # list[Point] 密集采样
    curve_type: str = "unknown"   # linear/exponential/polynomial...
    is_fit: bool = True


# 扩展 DataSeries
class DataSeriesExtended(BaseModel):
    name: str
    color_hex: Optional[str] = None
    points: list[PointWithError]
    has_error_bars: bool = False
    confidence: float = 1.0
```

## A.3 误差棒检测器 `extractors/error_bar.py`

```python
import cv2
import numpy as np
from core.schemas import ErrorBar, PointWithError
from calibration.calibrator import Calibrator


class ErrorBarDetector:
    """
    误差棒检测：
    针对已检测到的散点中心，在其垂直方向搜索连续的细线段（误差棒主干），
    并检测两端的水平"帽子"（cap）以确定误差棒端点。
    """

    def __init__(self, cap_search_width: int = 15,
                 min_bar_length: int = 4):
        self.cap_search_width = cap_search_width
        self.min_bar_length = min_bar_length

    def detect(self, mask: np.ndarray, point_centers: list[tuple],
               calibrator: Calibrator,
               direction: str = "vertical") -> list[PointWithError]:
        """
        mask: 该系列颜色的二值掩码
        point_centers: 数据点中心像素坐标 [(cx, cy), ...]
        direction: vertical(y误差) 或 horizontal(x误差)
        """
        results = []
        for (cx, cy) in point_centers:
            if direction == "vertical":
                err = self._detect_vertical(mask, cx, cy, calibrator)
            else:
                err = self._detect_horizontal(mask, cx, cy, calibrator)

            data_pt = calibrator.pixel_to_data(cx, cy)
            results.append(PointWithError(
                x=data_pt.x, y=data_pt.y, error=err))
        return results

    def _detect_vertical(self, mask, cx, cy,
                         calibrator) -> ErrorBar | None:
        """
        在数据点上下沿竖直方向追踪误差棒主干。
        从中心点向上、向下分别扫描，找到连续白色像素的最远端。
        """
        cx, cy = int(cx), int(cy)
        h, w = mask.shape

        # 向上追踪
        upper_y = self._trace_vertical(mask, cx, cy, step=-1)
        # 向下追踪
        lower_y = self._trace_vertical(mask, cx, cy, step=+1)

        # 验证：是否存在帽子（cap）增强可信度
        has_upper_cap = self._has_horizontal_cap(mask, cx, upper_y)
        has_lower_cap = self._has_horizontal_cap(mask, cx, lower_y)

        # 误差棒长度需达到阈值
        up_len = abs(cy - upper_y)
        lo_len = abs(lower_y - cy)
        if up_len < self.min_bar_length and lo_len < self.min_bar_length:
            return None

        # 转换为数据坐标的误差值
        center_data = calibrator.pixel_to_data(cx, cy)
        upper_data = calibrator.pixel_to_data(cx, upper_y)
        lower_data = calibrator.pixel_to_data(cx, lower_y)

        err = ErrorBar(
            y_err_upper=abs(upper_data.y - center_data.y)
                if (up_len >= self.min_bar_length) else None,
            y_err_lower=abs(center_data.y - lower_data.y)
                if (lo_len >= self.min_bar_length) else None,
        )
        return err

    def _trace_vertical(self, mask, cx, cy, step) -> int:
        """从 (cx,cy) 沿竖直方向追踪连续白色像素，返回端点 y"""
        h, w = mask.shape
        y = cy
        gap_tolerance = 2   # 允许小间隙（标记遮挡）
        gap_count = 0
        last_white = cy

        while 0 <= y < h:
            # 在 cx 附近 ±1 容差内检查（误差棒可能有1px偏移）
            band = mask[y, max(0, cx-1):min(w, cx+2)]
            if np.any(band > 0):
                last_white = y
                gap_count = 0
            else:
                gap_count += 1
                if gap_count > gap_tolerance:
                    break
            y += step
        return last_white

    def _has_horizontal_cap(self, mask, cx, cap_y) -> bool:
        """检测误差棒端点处是否有水平帽子线"""
        h, w = mask.shape
        cap_y = int(cap_y)
        if not (0 <= cap_y < h):
            return False
        x0 = max(0, cx - self.cap_search_width)
        x1 = min(w, cx + self.cap_search_width)
        row = mask[cap_y, x0:x1]
        # 帽子：连续白色像素宽度超过阈值
        white_run = self._max_consecutive(row > 0)
        return white_run >= 5

    def _detect_horizontal(self, mask, cx, cy,
                           calibrator) -> ErrorBar | None:
        """水平误差棒（x方向），逻辑对称"""
        cx, cy = int(cx), int(cy)
        left_x = self._trace_horizontal(mask, cx, cy, step=-1)
        right_x = self._trace_horizontal(mask, cx, cy, step=+1)

        left_len = abs(cx - left_x)
        right_len = abs(right_x - cx)
        if left_len < self.min_bar_length and right_len < self.min_bar_length:
            return None

        center_data = calibrator.pixel_to_data(cx, cy)
        left_data = calibrator.pixel_to_data(left_x, cy)
        right_data = calibrator.pixel_to_data(right_x, cy)

        return ErrorBar(
            x_err_left=abs(center_data.x - left_data.x)
                if left_len >= self.min_bar_length else None,
            x_err_right=abs(right_data.x - center_data.x)
                if right_len >= self.min_bar_length else None,
        )

    def _trace_horizontal(self, mask, cx, cy, step) -> int:
        h, w = mask.shape
        x = cx
        gap_tolerance, gap_count = 2, 0
        last_white = cx
        while 0 <= x < w:
            band = mask[max(0, cy-1):min(h, cy+2), x]
            if np.any(band > 0):
                last_white = x
                gap_count = 0
            else:
                gap_count += 1
                if gap_count > gap_tolerance:
                    break
            x += step
        return last_white

    @staticmethod
    def _max_consecutive(bool_arr: np.ndarray) -> int:
        """最长连续 True 段长度"""
        max_run = run = 0
        for v in bool_arr:
            if v:
                run += 1
                max_run = max(max_run, run)
            else:
                run = 0
        return max_run
```

## A.4 拟合曲线 vs 数据点判别 `extractors/fit_curve.py`

```python
import cv2
import numpy as np
from scipy.optimize import curve_fit
from core.schemas import FitCurve, Point
from calibration.calibrator import Calibrator


class FitCurveAnalyzer:
    """
    区分拟合曲线与离散数据点，并识别拟合函数类型。
    """

    # 平滑度阈值：二阶差分归一化后小于此值视为平滑曲线
    SMOOTHNESS_THRESHOLD = 0.05
    # 连续性阈值：有效列占比超过此值视为连续曲线
    CONTINUITY_THRESHOLD = 0.85

    def is_fit_curve(self, mask: np.ndarray) -> bool:
        """
        判别一个颜色掩码是拟合曲线还是数据点集合。
        依据：连续性 + 平滑度 + 标记缺失。
        """
        continuity = self._continuity_ratio(mask)
        if continuity < self.CONTINUITY_THRESHOLD:
            return False  # 不连续 → 离散数据点

        smoothness = self._smoothness(mask)
        marker_score = self._marker_likelihood(mask)

        # 高连续 + 高平滑 + 低标记可能性 → 拟合曲线
        return (smoothness < self.SMOOTHNESS_THRESHOLD
                and marker_score < 0.3)

    def _continuity_ratio(self, mask: np.ndarray) -> float:
        """有数据像素的列占总列数比例"""
        cols_with_data = np.sum(np.any(mask > 0, axis=0))
        total_cols = np.sum(np.any(mask > 0, axis=0).astype(bool)) or 1
        # 用掩码 x 范围内的覆盖率
        xs = np.where(np.any(mask > 0, axis=0))[0]
        if len(xs) < 2:
            return 0.0
        span = xs.max() - xs.min() + 1
        return cols_with_data / span

    def _smoothness(self, mask: np.ndarray) -> float:
        """提取曲线后计算二阶差分的归一化均值"""
        ys = self._extract_curve_y(mask)
        if len(ys) < 3:
            return 1.0
        ys = np.array(ys, dtype=float)
        second_diff = np.abs(np.diff(ys, 2))
        norm = (np.std(ys) + 1e-9)
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
        """
        通过连通域分析判断是否存在规则标记（圆/方块）。
        标记多 → 数据点；几乎无独立标记 → 曲线。
        """
        n, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask, connectivity=8)
        if n <= 1:
            return 0.0
        # 统计"圆形度高且面积适中"的连通域
        marker_count = 0
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            w_ = stats[i, cv2.CC_STAT_WIDTH]
            h_ = stats[i, cv2.CC_STAT_HEIGHT]
            if 10 <= area <= 400 and 0.5 <= w_ / max(h_, 1) <= 2.0:
                marker_count += 1
        # 归一化
        return min(1.0, marker_count / 10.0)

    def extract_fit_curve(self, mask: np.ndarray,
                          calibrator: Calibrator,
                          color_hex: str) -> FitCurve:
        """提取拟合曲线的密集采样点并识别函数类型"""
        ys_px = self._extract_curve_y(mask)
        xs_px = [px for px in range(mask.shape[1])
                 if np.any(mask[:, px] > 0)]

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
        """尝试拟合常见函数，返回 R² 最高者"""
        if len(points) < 5:
            return "unknown"
        x = np.array([p.x for p in points])
        y = np.array([p.y for p in points])

        candidates = {
            "linear": (lambda x, a, b: a * x + b, 2),
            "quadratic": (lambda x, a, b, c: a*x**2 + b*x + c, 3),
            "exponential":
                (lambda x, a, b, c: a * np.exp(b * x) + c, 3),
            "logarithmic":
                (lambda x, a, b: a * np.log(np.abs(x) + 1e-9) + b, 2),
            "power": (lambda x, a, b: a * np.power(np.abs(x) + 1e-9, b), 2),
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

        # R² 太低也算 unknown
        return best_type if best_r2 > 0.9 else "unknown"

    @staticmethod
    def _r_squared(y, y_pred) -> float:
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2) + 1e-12
        return 1.0 - ss_res / ss_tot
```

其中拟合优度 \(R^2\) 定义为：

\[
R^2 = 1 - \frac{\sum_i (y_i - \hat{y}_i)^2}{\sum_i (y_i - \bar{y})^2}
\]

## A.5 集成到散点提取器 `extractors/scatter.py`（增强版）

```python
import cv2
import numpy as np
from extractors.base import BaseExtractor
from extractors.color_segmentation import segment_by_color
from extractors.error_bar import ErrorBarDetector
from extractors.fit_curve import FitCurveAnalyzer
from core.schemas import DataSeries, Point


class ScatterExtractor(BaseExtractor):
    """增强版散点提取：含误差棒与拟合曲线分离"""

    def __init__(self):
        self.error_detector = ErrorBarDetector()
        self.fit_analyzer = FitCurveAnalyzer()

    def extract(self, img, calibrator, series_colors=None,
                detect_errors=True, separate_fits=True):
        plot_mask = self._build_plot_mask(img, calibrator)
        color_masks = segment_by_color(img, plot_mask,
                                       given_colors=series_colors)

        data_series, fit_curves = [], []

        for color_hex, mask in color_masks.items():
            # 1. 先判断这是拟合曲线还是数据点
            if separate_fits and self.fit_analyzer.is_fit_curve(mask):
                fit = self.fit_analyzer.extract_fit_curve(
                    mask, calibrator, color_hex)
                fit_curves.append(fit)
                continue

            # 2. 检测散点中心
            centers = self._detect_points(mask)
            if not centers:
                continue

            # 3. 误差棒检测
            if detect_errors:
                points_with_err = self.error_detector.detect(
                    mask, centers, calibrator, direction="vertical")
                has_err = any(p.error is not None
                              for p in points_with_err)
                # 转回标准 Point（误差信息存入 metadata）
                points = [Point(x=p.x, y=p.y) for p in points_with_err]
            else:
                points = [calibrator.pixel_to_data(cx, cy)
                          for cx, cy in centers]
                has_err = False

            if points:
                series = DataSeries(
                    name=f"series_{color_hex}",
                    color_hex=color_hex,
                    points=points,
                    confidence=0.9,
                )
                # 误差信息附加到 metadata（schema 可扩展）
                data_series.append(series)

        # fit_curves 通过 metadata 返回（在 orchestrator 合并）
        self._last_fit_curves = fit_curves
        self._last_errors = (points_with_err
                             if detect_errors and 'points_with_err'
                             in dir() else [])
        return data_series

    def _detect_points(self, mask):
        n, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask, connectivity=8)
        centers = []
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            w_ = stats[i, cv2.CC_STAT_WIDTH]
            h_ = stats[i, cv2.CC_STAT_HEIGHT]
            # 过滤：排除细长的误差棒主干（高宽比极端）
            aspect = w_ / max(h_, 1)
            if 5 <= area <= 800 and 0.3 <= aspect <= 3.0:
                cx, cy = centroids[i]
                centers.append((float(cx), float(cy)))
        return centers

    def _build_plot_mask(self, img, calibrator):
        from extractors.line_chart import LineChartExtractor
        return LineChartExtractor()._build_plot_mask(img, calibrator)
```

---

# 模块 B：本地 VLM 部署

提供**完全离线**的 VLM 方案，适合数据隐私敏感场景。涵盖 GPU/CPU 配置、量化、显存优化。

