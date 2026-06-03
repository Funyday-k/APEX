from core.schemas import ChartType, HeatmapOptions
from extractors.bar_chart import BarChartExtractor
from extractors.box_plot import BoxPlotExtractor
from extractors.heatmap import HeatmapExtractor
from extractors.line_chart import LineChartExtractor
from extractors.scatter import ScatterExtractor

_REGISTRY = {
    ChartType.LINE: LineChartExtractor,
    ChartType.SCATTER: ScatterExtractor,
    ChartType.BAR: BarChartExtractor,
    ChartType.HEATMAP: HeatmapExtractor,
    ChartType.BOX: BoxPlotExtractor,
}


def get_extractor(chart_type: ChartType):
    cls = _REGISTRY.get(chart_type, LineChartExtractor)
    return cls()
