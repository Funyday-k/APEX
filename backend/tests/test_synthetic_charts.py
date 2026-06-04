"""End-to-end extraction tests on matplotlib-rendered charts."""

import pytest

from calibration.calibrator import Calibrator
from core.schemas import CalibrationConfig, ChartType, HeatmapOptions
from extractors import get_extractor
from tests.benchmark.metrics import point_count, series_count, x_coverage
from tests.fixtures.synthetic import (
    render_bar_chart,
    render_box_plot,
    render_heatmap,
    render_line_chart,
    render_line_with_band,
    render_scatter_with_error,
)

pytest.importorskip("matplotlib")


def _calibrator_from_truth(truth: dict) -> Calibrator:
    cal_dict = truth["calibration"]
    return Calibrator(CalibrationConfig.model_validate(cal_dict))


@pytest.mark.parametrize(
    "xscale,yscale",
    [("linear", "linear"), ("log", "log"), ("linear", "log")],
)
def test_synthetic_line_extraction(xscale, yscale):
    rgb, _, truth = render_line_chart(xscale=xscale, yscale=yscale, n_series=1, seed=42)
    cal = _calibrator_from_truth(truth)
    ext = get_extractor(ChartType.LINE)
    series = ext.extract(rgb, cal, regions=None)
    assert series_count(series) >= 1
    assert point_count(series) >= 5
    x_lo, x_hi = truth["x_range"]
    cov = x_coverage(series[0], float(x_lo), float(x_hi))
    assert cov >= 0.35


@pytest.mark.parametrize("legend_loc", ["upper right", "lower left", "upper left"])
def test_synthetic_line_legend_positions(legend_loc):
    rgb, _, truth = render_line_chart(legend_loc=legend_loc, n_series=2, seed=7)
    cal = _calibrator_from_truth(truth)
    series = get_extractor(ChartType.LINE).extract(rgb, cal, regions=None)
    assert point_count(series) >= 3


def test_synthetic_scatter_extraction():
    rgb, _, truth = render_scatter_with_error(seed=3)
    cal = _calibrator_from_truth(truth)
    series = get_extractor(ChartType.SCATTER).extract(rgb, cal, regions=None)
    assert series_count(series) >= 1
    assert point_count(series) >= 3


def test_synthetic_bar_extraction():
    rgb, _, truth = render_bar_chart(seed=11)
    cal = _calibrator_from_truth(truth)
    series = get_extractor(ChartType.BAR).extract(rgb, cal, regions=None)
    assert series_count(series) >= 1
    assert point_count(series) >= 2


def test_synthetic_box_extraction():
    rgb, _, truth = render_box_plot(seed=5)
    cal = _calibrator_from_truth(truth)
    series = get_extractor(ChartType.BOX).extract(rgb, cal, regions=None)
    assert series_count(series) >= 1


def test_synthetic_heatmap_extraction():
    rgb, _, truth = render_heatmap(seed=9)
    cal = _calibrator_from_truth(truth)
    opts = HeatmapOptions(
        colorbar_box=truth["colorbar_box"],
        value_range=truth["value_range"],
        grid=(4, 5),
    )
    series = get_extractor(ChartType.HEATMAP).extract(rgb, cal, heatmap_options=opts)
    assert series_count(series) == 1
    assert point_count(series) == 20


def test_synthetic_line_with_band_detector():
    from extractors.error_band import ErrorBandDetector
    from extractors.color_segmentation import segment_by_color

    rgb, _, truth = render_line_with_band(seed=2)
    cal = _calibrator_from_truth(truth)
    masks = segment_by_color(rgb, tolerance=40)
    assert masks
    det = ErrorBandDetector()
    xt = cal.x_transform
    x_min, x_max = int(min(xt.p1, xt.p2)), int(max(xt.p1, xt.p2))
    band = det.detect_in_mask(rgb, masks[0], cal, x_min, x_max, "#0000ff", "band")
    # Band may or may not detect on matplotlib fill; at least no crash
    assert band is None or len(band.upper_points) >= 2
