from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChartType(str, Enum):
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HEATMAP = "heatmap"
    BOX = "box"
    PIE = "pie"
    CONTOUR = "contour"
    MICROSCOPY = "microscopy"
    UNKNOWN = "unknown"


class AxisScale(str, Enum):
    LINEAR = "linear"
    LOG = "log"
    TIME = "time"


class Point(BaseModel):
    x: float
    y: float


class ErrorBar(BaseModel):
    y_err_upper: Optional[float] = None
    y_err_lower: Optional[float] = None
    x_err_left: Optional[float] = None
    x_err_right: Optional[float] = None


class PointWithError(BaseModel):
    x: float
    y: float
    error: Optional[ErrorBar] = None


class FitCurve(BaseModel):
    name: str
    color_hex: Optional[str] = None
    points: list[Point]
    curve_type: str = "unknown"
    is_fit: bool = True


class CalibrationPoint(BaseModel):
    pixel: Point
    data: Point


class AxisCalibration(BaseModel):
    scale: AxisScale = AxisScale.LINEAR
    ref1: CalibrationPoint
    ref2: CalibrationPoint
    label: Optional[str] = None
    unit: Optional[str] = None


class CalibrationConfig(BaseModel):
    x_axis: AxisCalibration
    y_axis: AxisCalibration


class DataSeries(BaseModel):
    name: str
    color_hex: Optional[str] = None
    points: list[Point]
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    has_error_bars: bool = False
    errors: list[Optional[ErrorBar]] = Field(default_factory=list)


class HeatmapOptions(BaseModel):
    colorbar_box: dict[str, int]
    value_range: tuple[float, float]
    grid: tuple[int, int] = (10, 10)


class ExtractionResult(BaseModel):
    chart_type: ChartType
    series: list[DataSeries]
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    legend: list[str] = []
    metadata: dict[str, Any] = {}
    overall_confidence: float = 1.0
    low_confidence_flags: list[str] = []
