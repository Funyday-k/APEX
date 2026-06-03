import numpy as np

from core.schemas import AxisCalibration, AxisScale


class AxisTransform:
    def __init__(self, cal: AxisCalibration, is_x: bool = True):
        self.scale = cal.scale
        self.is_x = is_x

        if is_x:
            self.p1, self.p2 = cal.ref1.pixel.x, cal.ref2.pixel.x
            self.d1, self.d2 = cal.ref1.data.x, cal.ref2.data.x
        else:
            self.p1, self.p2 = cal.ref1.pixel.y, cal.ref2.pixel.y
            self.d1, self.d2 = cal.ref1.data.y, cal.ref2.data.y

        if self.scale == AxisScale.LOG:
            if self.d1 <= 0 or self.d2 <= 0:
                raise ValueError("对数轴标定数据值必须为正")
            self.d1 = np.log10(self.d1)
            self.d2 = np.log10(self.d2)

        if self.p2 == self.p1:
            raise ValueError("两个标定点像素坐标不能相同")

        self.slope = (self.d2 - self.d1) / (self.p2 - self.p1)

    def pixel_to_data(self, p: float) -> float:
        d = self.d1 + (p - self.p1) * self.slope
        if self.scale == AxisScale.LOG:
            return float(10**d)
        return float(d)

    def data_to_pixel(self, d: float) -> float:
        if self.scale == AxisScale.LOG:
            d = np.log10(d)
        return float(self.p1 + (d - self.d1) / self.slope)
