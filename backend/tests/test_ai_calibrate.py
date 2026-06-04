"""Tests for AI calibration fusion and orchestration."""

from unittest.mock import AsyncMock, patch

import numpy as np

from calibration.ai_calibrate import ai_auto_calibrate, fuse_ticks


def test_fuse_ticks_prefers_vlm_values_at_same_pixel():
    cv = {
        "x_ticks": [{"pixel": 100.0, "value": 0.0}, {"pixel": 300.0, "value": 10.0}],
        "y_ticks": [{"pixel": 50.0, "value": 0.0}, {"pixel": 150.0, "value": 5.0}],
    }
    vlm = {
        "coord_space": "pixel",
        "x_ticks": [
            {"value": 0.5, "position": {"x": 105, "y": 200}},
            {"value": 9.8, "position": {"x": 298, "y": 200}},
        ],
        "y_ticks": [
            {"value": 0.2, "position": {"x": 40, "y": 52}},
            {"value": 5.1, "position": {"x": 40, "y": 148}},
        ],
    }
    axes = {"x_axis": {"y_pixel": 200}, "y_axis": {"x_pixel": 40}}
    merged = fuse_ticks(cv, vlm, 400, 300, axes)
    assert abs(merged["x_ticks"][0]["value"] - 0.5) < 1e-6
    assert abs(merged["y_ticks"][1]["value"] - 5.1) < 1e-6


def test_fuse_ticks_cv_only_when_vlm_empty():
    cv = {"x_ticks": [{"pixel": 10.0, "value": 1.0}], "y_ticks": []}
    merged = fuse_ticks(cv, {}, 100, 100, {})
    assert merged["x_ticks"][0]["value"] == 1.0


async def _run_cv_fallback():
    img = np.ones((120, 200, 3), dtype=np.uint8) * 255
    import cv2

    cv2.line(img, (30, 100), (180, 100), (0, 0, 0), 2)
    cv2.line(img, (30, 20), (30, 100), (0, 0, 0), 2)
    for x, val in [(50, "0"), (100, "5"), (150, "10")]:
        cv2.putText(img, val, (x - 5, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
    for y, val in [(80, "0"), (50, "5"), (25, "10")]:
        cv2.putText(img, val, (5, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

    from PIL import Image
    import io

    bio = io.BytesIO()
    Image.fromarray(img).save(bio, format="PNG")
    image_bytes = bio.getvalue()

    with patch("calibration.ai_calibrate.get_vlm_provider") as mock_vlm:
        prov = mock_vlm.return_value
        prov.read_axis_ticks = AsyncMock(return_value={})
        result = await ai_auto_calibrate(image_bytes, use_vlm=True)
    return result


def test_ai_auto_calibrate_cv_fallback():
    import asyncio

    result = asyncio.run(_run_cv_fallback())
    assert "source" in result
    assert result["source"] in ("cv", "vlm")
    assert "ticks" in result


async def _run_vlm_ticks():
    img = np.ones((100, 160, 3), dtype=np.uint8) * 255
    from PIL import Image
    import io

    bio = io.BytesIO()
    Image.fromarray(img).save(bio, format="PNG")
    image_bytes = bio.getvalue()

    vlm_resp = {
        "x_scale": "linear",
        "y_scale": "linear",
        "x_ticks": [
            {"value": 0.0, "position": {"x": 0.2, "y": 0.9}},
            {"value": 1.0, "position": {"x": 0.8, "y": 0.9}},
        ],
        "y_ticks": [
            {"value": 0.0, "position": {"x": 0.1, "y": 0.85}},
            {"value": 1.0, "position": {"x": 0.1, "y": 0.15}},
        ],
    }

    with patch("calibration.ai_calibrate.get_vlm_provider") as mock_vlm:
        prov = mock_vlm.return_value
        prov.read_axis_ticks = AsyncMock(return_value=vlm_resp)
        result = await ai_auto_calibrate(image_bytes, use_vlm=True)
    return result


def test_ai_auto_calibrate_with_vlm_ticks():
    import asyncio

    result = asyncio.run(_run_vlm_ticks())
    assert result["source"] == "vlm"
