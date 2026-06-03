import numpy as np

from core.schemas import BBox, PlotRegion, PlotRegions
from extractors.plot_mask import build_plot_mask
from preprocessing.region_fusion import parse_vlm_regions, point_in_regions, regions_for_mask
from tests.test_calibration import make_calibration
from calibration.calibrator import Calibrator


def test_parse_vlm_regions_normalized():
    raw = {
        "coord_space": "normalized",
        "regions": [
            {
                "kind": "legend",
                "bbox": {"x0": 0.7, "y0": 0.05, "x1": 0.95, "y1": 0.2},
                "confidence": 0.9,
            }
        ],
    }
    pr = parse_vlm_regions(raw, 400, 200)
    assert len(pr.regions) == 1
    assert pr.regions[0].kind == "legend"
    assert pr.regions[0].bbox.x0 == 280


def test_build_plot_mask_excludes_legend():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    for x in range(50, 300):
        y = int(120 - (x - 50) * 0.15)
        img[y - 1 : y + 2, x, :] = [200, 40, 40]
    cv2 = __import__("cv2")
    cv2.circle(img, (340, 30), 6, (40, 40, 200), -1)

    cal = Calibrator(make_calibration())
    regions = PlotRegions(
        regions=[
            PlotRegion(
                kind="legend",
                bbox=BBox(x0=300, y0=0, x1=399, y1=60),
            )
        ],
        image_width=400,
        image_height=200,
    )
    mask_plain = build_plot_mask(img, cal, regions=None)
    mask_excl = build_plot_mask(img, cal, regions=regions)
    assert cv2.countNonZero(mask_plain) >= cv2.countNonZero(mask_excl)


def test_point_in_regions():
    regions = [
        PlotRegion(kind="legend", bbox=BBox(x0=10, y0=10, x1=50, y1=50)),
    ]
    assert point_in_regions(25, 25, regions)
    assert not point_in_regions(5, 5, regions)
