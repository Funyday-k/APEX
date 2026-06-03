from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

RegionKind = Literal[
    "plot_area",
    "legend",
    "x_axis",
    "y_axis",
    "x_tick_labels",
    "y_tick_labels",
    "title",
    "colorbar",
    "other_text",
]


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


class BBox(BaseModel):
    """Pixel bbox in image coordinates: x0,y0 top-left, x1,y1 bottom-right."""

    x0: int
    y0: int
    x1: int
    y1: int
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class PlotRegion(BaseModel):
    kind: RegionKind
    bbox: BBox
    label: Optional[str] = None


class PlotRegions(BaseModel):
    regions: list[PlotRegion] = Field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    source: str = "vlm"


class ChartMetadata(BaseModel):
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x_quantity: Optional[str] = None
    y_quantity: Optional[str] = None
    x_unit: Optional[str] = None
    y_unit: Optional[str] = None
    x_scale: str = "linear"
    y_scale: str = "linear"
    legend: list[str] = Field(default_factory=list)


class PointRemovalSuggestion(BaseModel):
    series_idx: int
    point_idx: int
    pixel_x: float
    pixel_y: float
    reason: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class ExtractionResult(BaseModel):
    chart_type: ChartType
    series: list[DataSeries]
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x_quantity: Optional[str] = None
    y_quantity: Optional[str] = None
    x_unit: Optional[str] = None
    y_unit: Optional[str] = None
    legend: list[str] = []
    regions: Optional[PlotRegions] = None
    suggested_removals: list[PointRemovalSuggestion] = Field(default_factory=list)
    metadata: dict[str, Any] = {}
    overall_confidence: float = 1.0
    low_confidence_flags: list[str] = []
