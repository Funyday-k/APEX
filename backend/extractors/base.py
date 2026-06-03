from abc import ABC, abstractmethod

import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import DataSeries


class BaseExtractor(ABC):
    @abstractmethod
    def extract(
        self,
        img: np.ndarray,
        calibrator: Calibrator,
        series_colors: list[str] | None = None,
    ) -> list[DataSeries]:
        ...
