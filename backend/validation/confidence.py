import numpy as np

from core.schemas import DataSeries


def coverage_score(series: DataSeries, expected_range: tuple) -> float:
    if not series.points:
        return 0.0
    xs = [p.x for p in series.points]
    x_min, x_max = expected_range
    if x_max == x_min:
        return 1.0
    covered = (max(xs) - min(xs)) / (x_max - x_min)
    return float(min(1.0, covered))


def smoothness_score(series: DataSeries) -> float:
    if len(series.points) < 3:
        return 0.8
    ys = np.array([p.y for p in series.points])
    second_diff = np.abs(np.diff(ys, 2))
    norm = np.std(ys) + 1e-9
    noise_ratio = np.mean(second_diff) / norm
    return float(np.clip(1.0 - noise_ratio, 0.0, 1.0))


def agreement_score(cv_count: int, vlm_legend_count: int) -> float:
    if vlm_legend_count == 0:
        return 0.7
    diff = abs(cv_count - vlm_legend_count)
    return float(max(0.0, 1.0 - diff / max(cv_count, vlm_legend_count, 1)))
