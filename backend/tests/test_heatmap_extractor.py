import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import AxisCalibration, AxisScale, CalibrationConfig, CalibrationPoint, HeatmapOptions, Point
from extractors.heatmap import HeatmapExtractor


def _calibrator():
    return Calibrator(
        CalibrationConfig(
            x_axis=AxisCalibration(
                scale=AxisScale.LINEAR,
                ref1=CalibrationPoint(
                    pixel=Point(x=50, y=350), data=Point(x=0, y=0)
                ),
                ref2=CalibrationPoint(
                    pixel=Point(x=450, y=350), data=Point(x=10, y=0)
                ),
            ),
            y_axis=AxisCalibration(
                scale=AxisScale.LINEAR,
                ref1=CalibrationPoint(
                    pixel=Point(x=50, y=350), data=Point(x=0, y=0)
                ),
                ref2=CalibrationPoint(
                    pixel=Point(x=50, y=50), data=Point(x=0, y=10)
                ),
            ),
        )
    )


def test_heatmap_grid_sampling():
    img = np.zeros((400, 500, 3), dtype=np.uint8)
    for y in range(50, 350):
        for x in range(50, 450):
            t = (x - 50) / 400
            img[y, x] = [int(255 * t), int(128 * (1 - t)), 64]
    cbar = {"x0": 460, "y0": 50, "x1": 490, "y1": 350}
    opts = HeatmapOptions(colorbar_box=cbar, value_range=(0.0, 1.0), grid=(3, 4))
    series = HeatmapExtractor().extract(img, _calibrator(), heatmap_options=opts)
    assert len(series) == 1
    assert len(series[0].points) == 12
