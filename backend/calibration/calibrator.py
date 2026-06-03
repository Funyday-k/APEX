import numpy as np

from calibration.transforms import AxisTransform
from core.schemas import CalibrationConfig, Point


class Calibrator:
    def __init__(self, config: CalibrationConfig):
        self.x_transform = AxisTransform(config.x_axis, is_x=True)
        self.y_transform = AxisTransform(config.y_axis, is_x=False)

    def pixel_to_data(self, px: float, py: float) -> Point:
        return Point(
            x=self.x_transform.pixel_to_data(px),
            y=self.y_transform.pixel_to_data(py),
        )

    def data_to_pixel(self, x: float, y: float) -> Point:
        return Point(
            x=self.x_transform.data_to_pixel(x),
            y=self.y_transform.data_to_pixel(y),
        )

    def batch_pixel_to_data(self, pixels: np.ndarray) -> np.ndarray:
        out = np.empty_like(pixels, dtype=float)
        for i, (px, py) in enumerate(pixels):
            p = self.pixel_to_data(px, py)
            out[i] = [p.x, p.y]
        return out
