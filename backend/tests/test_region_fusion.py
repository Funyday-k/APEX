import numpy as np

from calibration.axis_detector import detect_axes
from core.schemas import BBox, PlotRegion, PlotRegions
from extractors.plot_mask import build_plot_mask
from preprocessing.region_fusion import (
    axis_confidence_from_geometry,
    bbox_iou,
    merge_axis_regions,
    merge_plot_area,
    parse_vlm_regions,
    point_in_regions,
    regions_for_mask,
)
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
    assert pr.regions[0].source == "vlm"


def test_bbox_iou():
    a = BBox(x0=0, y0=0, x1=100, y1=100)
    b = BBox(x0=50, y0=50, x1=150, y1=150)
    assert 0.14 < bbox_iou(a, b) < 0.25


def test_merge_plot_area_fuses_when_both_present():
    vlm = PlotRegions(
        regions=[
            PlotRegion(
                kind="plot_area",
                bbox=BBox(x0=40, y0=30, x1=360, y1=180, confidence=0.55),
                source="vlm",
            )
        ],
        image_width=400,
        image_height=200,
    )
    cv_plot = {"x0": 50, "y0": 35, "x1": 350, "y1": 175, "detected": True}
    merged = merge_plot_area(vlm, cv_plot, 400, 200)
    plot = [r for r in merged.regions if r.kind == "plot_area"]
    assert len(plot) == 1
    assert plot[0].source in ("fused", "cv", "vlm")


def test_merge_axis_regions_adds_cv_axes():
    regions = PlotRegions(image_width=400, image_height=200)
    axis_geometry = {
        "x_axis": {"y_pixel": 170, "x_start": 50, "x_end": 350, "confidence": 0.8},
        "y_axis": {"x_pixel": 45, "y_start": 30, "y_end": 170, "confidence": 0.75},
        "x_axis_bbox": {"x0": 50, "y0": 166, "x1": 350, "y1": 174},
        "y_axis_bbox": {"x0": 41, "y0": 30, "x1": 49, "y1": 170},
    }
    merged = merge_axis_regions(regions, axis_geometry, 400, 200)
    kinds = {r.kind for r in merged.regions}
    assert "x_axis" in kinds
    assert "y_axis" in kinds


def test_axis_confidence_from_geometry():
    axes = {
        "x_axis": {"confidence": 0.7},
        "y_axis": {"confidence": 0.8},
    }
    conf = axis_confidence_from_geometry(axes, {"detected": True})
    assert conf["x_axis"] == 0.7
    assert conf["plot_area"] == 0.75


def test_detect_axes_refines_from_plot_area():
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    cv2 = __import__("cv2")
    # Draw axes
    cv2.line(img, (50, 170), (350, 170), (0, 0, 0), 2)
    cv2.line(img, (50, 30), (50, 170), (0, 0, 0), 2)
    plot_area = {"x0": 50, "y0": 30, "x1": 350, "y1": 170, "detected": True}
    axes = detect_axes(img, plot_area)
    assert 160 <= axes["x_axis"]["y_pixel"] <= 175
    assert 45 <= axes["y_axis"]["x_pixel"] <= 55
    assert "x_axis_bbox" in axes


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
