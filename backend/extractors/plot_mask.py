"""Shared plot ROI from calibration and optional auto-detected plot area."""

import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import PlotRegion, PlotRegions
from preprocessing.grid_suppress import foreground_data_mask
from preprocessing.plot_area import detect_plot_area
from preprocessing.region_fusion import regions_for_mask


def calibration_plot_bounds(calibrator: Calibrator) -> tuple[int, int, int, int]:
    xt, yt = calibrator.x_transform, calibrator.y_transform
    x0 = int(min(xt.p1, xt.p2))
    x1 = int(max(xt.p1, xt.p2))
    y0 = int(min(yt.p1, yt.p2))
    y1 = int(max(yt.p1, yt.p2))
    return x0, y0, x1, y1


def _subtract_regions(mask: np.ndarray, regions: list[PlotRegion], pad: int = 3) -> np.ndarray:
    h, w = mask.shape[:2]
    out = mask.copy()
    for r in regions:
        b = r.bbox
        x0 = max(0, b.x0 - pad)
        y0 = max(0, b.y0 - pad)
        x1 = min(w, b.x1 + pad)
        y1 = min(h, b.y1 + pad)
        if x1 > x0 and y1 > y0:
            cv2.rectangle(out, (x0, y0), (x1, y1), 0, -1)
    return out


def build_plot_mask(
    img: np.ndarray,
    calibrator: Calibrator,
    *,
    intersect_auto: bool = True,
    pad: int = 3,
    axis_inset_px: int = 2,
    suppress_grid: bool = True,
    regions: PlotRegions | None = None,
) -> np.ndarray:
    """
    Build foreground mask inside the calibrated plot area.
    Uses a small inset from calibration bounds; does not aggressively exclude axis strokes.
    """
    h, w = img.shape[:2]
    x0, y0, x1, y1 = calibration_plot_bounds(calibrator)

    x0 = min(w - 2, max(0, x0 + axis_inset_px))
    y0 = min(h - 2, max(0, y0 + axis_inset_px))
    x1 = min(w - 1, max(x0 + 1, x1 - axis_inset_px))
    y1 = min(h - 1, max(y0 + 1, y1 - axis_inset_px))

    if intersect_auto:
        auto = detect_plot_area(img)
        if auto.get("detected"):
            # Union vertical extent with auto plot (avoid clipping curve tops)
            x0 = max(x0, auto["x0"] + axis_inset_px)
            y0 = min(y0, auto["y0"] + axis_inset_px)
            x1 = min(x1, auto["x1"] - axis_inset_px)
            y1 = max(y1, auto["y1"] - axis_inset_px)

    mask = np.zeros((h, w), np.uint8)
    if x1 > x0 and y1 > y0:
        mask[
            max(0, y0 - pad) : min(h, y1 + pad),
            max(0, x0 - pad) : min(w, x1 + pad),
        ] = 255

    if suppress_grid:
        mask = foreground_data_mask(img, mask, axis_inset_px=axis_inset_px)

    exclude = regions_for_mask(regions)
    if exclude:
        mask = _subtract_regions(mask, exclude, pad=4)
    return mask


def plot_x_range(calibrator: Calibrator) -> tuple[int, int]:
    x0, _, x1, _ = calibration_plot_bounds(calibrator)
    return x0, x1
