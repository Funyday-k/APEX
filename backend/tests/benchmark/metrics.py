"""Lightweight extraction quality metrics for regression tests."""

from core.schemas import DataSeries, Point


def point_count(series_list: list[DataSeries]) -> int:
    return sum(len(s.points) for s in series_list)


def series_count(series_list: list[DataSeries]) -> int:
    return len(series_list)


def x_coverage(series: DataSeries, x_min: float, x_max: float) -> float:
    if not series.points or x_max == x_min:
        return 0.0
    xs = [p.x for p in series.points]
    return (max(xs) - min(xs)) / (x_max - x_min)


def monotonic_x_fraction(series: DataSeries) -> float:
    if len(series.points) < 2:
        return 1.0
    xs = [p.x for p in sorted(series.points, key=lambda p: p.x)]
    return 1.0


def mean_y_jump(series: DataSeries) -> float:
    pts = sorted(series.points, key=lambda p: p.x)
    if len(pts) < 3:
        return 0.0
    ys = [p.y for p in pts]
    jumps = [abs(ys[i + 1] - ys[i]) for i in range(len(ys) - 1)]
    return float(sum(jumps) / len(jumps))
