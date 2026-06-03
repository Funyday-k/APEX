import cv2
import numpy as np

from calibration.calibrator import Calibrator
from core.schemas import BBox, PlotRegion, PlotRegions
from extractors.scatter import ScatterExtractor
from tests.test_calibration import make_calibration


def test_scatter_excludes_markers_in_legend_region():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    # data markers in plot
    for x, y in [(80, 140), (120, 120), (160, 100)]:
        cv2.circle(img, (x, y), 5, (40, 120, 200), -1)
    # legend-like marker top-right
    cv2.circle(img, (350, 25), 5, (40, 120, 200), -1)

    cal = Calibrator(make_calibration())
    regions = PlotRegions(
        regions=[
            PlotRegion(
                kind="legend",
                bbox=BBox(x0=300, y0=0, x1=399, y1=80),
            )
        ],
        image_width=400,
        image_height=200,
    )
    ext = ScatterExtractor()
    series = ext.extract(img, cal, series_colors=["#2878c8"], regions=regions)
    assert len(series) >= 1
    pts = series[0].points
    # should not include point mapped from legend pixel (350, 25)
    assert len(pts) <= 4
    assert len(pts) >= 2
