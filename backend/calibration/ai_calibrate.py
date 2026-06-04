"""AI-assisted calibration: fuse CV/OCR ticks with optional VLM tick reading."""

from __future__ import annotations

from calibration.auto_calibrate import ticks_to_calibration_config
from calibration.axis_detector import detect_axes
from calibration.scale_detector import infer_axis_scales
from calibration.tick_detector import detect_ticks
from calibration.tick_parse import resolve_tick_value
from ocr.ocr_engine import OCREngine
from preprocessing.loader import load_image
from preprocessing.plot_area import constrain_plot_area_with_axes, detect_plot_area
from vlm.provider import get_vlm_provider


def _norm_pos_to_pixel(pos: dict, img_w: int, img_h: int, coord_space: str | None) -> tuple[float, float]:
    x = float(pos.get("x", 0))
    y = float(pos.get("y", 0))
    if coord_space == "normalized" or (0 <= x <= 1.01 and 0 <= y <= 1.01 and x <= 1 and y <= 1):
        return x * img_w, y * img_h
    return x, y


def _parse_vlm_ticks(
    vlm_raw: dict,
    axis: str,
    img_w: int,
    img_h: int,
    axes: dict,
) -> list[dict]:
    key = "x_ticks" if axis == "x" else "y_ticks"
    coord_space = vlm_raw.get("coord_space", "normalized")
    out: list[dict] = []
    for item in vlm_raw.get(key) or []:
        if not isinstance(item, dict):
            continue
        value = resolve_tick_value(item.get("value"), item.get("label_text"))
        if value is None:
            continue
        pos = item.get("position") or {}
        px, py = _norm_pos_to_pixel(pos, img_w, img_h, coord_space)
        if axis == "x":
            pixel = px
            y_line = (axes.get("x_axis") or {}).get("y_pixel")
            if y_line is not None:
                py = float(y_line)
        else:
            pixel = py
            x_line = (axes.get("y_axis") or {}).get("x_pixel")
            if x_line is not None:
                px = float(x_line)
        out.append({"pixel": float(pixel), "value": float(value)})
    return sorted(out, key=lambda t: t["pixel"])


def fuse_ticks(
    cv_ticks: dict,
    vlm_raw: dict | None,
    img_w: int,
    img_h: int,
    axes: dict,
    merge_px: float = 18.0,
) -> dict:
    """Merge CV/OCR tick positions with VLM-read values."""
    vlm_raw = vlm_raw or {}
    vlm_x = _parse_vlm_ticks(vlm_raw, "x", img_w, img_h, axes)
    vlm_y = _parse_vlm_ticks(vlm_raw, "y", img_w, img_h, axes)

    return {
        "x_ticks": _merge_axis_ticks(cv_ticks.get("x_ticks") or [], vlm_x, merge_px),
        "y_ticks": _merge_axis_ticks(cv_ticks.get("y_ticks") or [], vlm_y, merge_px),
    }


def _merge_axis_ticks(
    cv_list: list[dict],
    vlm_list: list[dict],
    merge_px: float,
) -> list[dict]:
    if not vlm_list:
        return list(cv_list)
    if not cv_list:
        return list(vlm_list)

    merged = [dict(t) for t in cv_list]
    for vt in vlm_list:
        if merged:
            best_i = min(
                range(len(merged)),
                key=lambda i: abs(merged[i]["pixel"] - vt["pixel"]),
            )
            if abs(merged[best_i]["pixel"] - vt["pixel"]) < merge_px:
                merged[best_i]["value"] = vt["value"]
                continue
        merged.append(dict(vt))
    return sorted(merged, key=lambda t: t["pixel"])


async def ai_auto_calibrate(image_bytes: bytes, *, use_vlm: bool = True) -> dict:
    """Run CV+OCR tick detection, optionally fuse VLM tick values, return calibration payload."""
    img = load_image(image_bytes)
    h, w = img.shape[:2]
    ocr = OCREngine().extract(img)

    rough_plot = detect_plot_area(img)
    rough_axes = detect_axes(img, rough_plot)
    pre_ticks = detect_ticks(img, rough_axes, ocr)
    x_tick_px = [int(t["pixel"]) for t in pre_ticks.get("x_ticks", [])]
    plot_area = detect_plot_area(img, x_tick_pixels=x_tick_px or None)
    axes = detect_axes(img, plot_area)
    plot_area = constrain_plot_area_with_axes(plot_area, axes, w, h)

    cv_ticks = detect_ticks(img, axes, ocr)
    for t in cv_ticks.get("x_ticks", []):
        if "label_text" not in t:
            t["value"] = resolve_tick_value(t.get("value"), None)
    for t in cv_ticks.get("y_ticks", []):
        if "label_text" not in t:
            t["value"] = resolve_tick_value(t.get("value"), None)

    vlm_raw: dict = {}
    if use_vlm:
        vlm = get_vlm_provider()
        vlm_raw = await vlm.read_axis_ticks(image_bytes) or {}

    ticks = fuse_ticks(cv_ticks, vlm_raw, w, h, axes)
    source = "vlm" if (vlm_raw.get("x_ticks") or vlm_raw.get("y_ticks")) else "cv"

    scale_info = infer_axis_scales(
        ticks,
        vlm_x_scale=vlm_raw.get("x_scale"),
        vlm_y_scale=vlm_raw.get("y_scale"),
    )
    x_scale = scale_info.get("x_scale", "linear")
    y_scale = scale_info.get("y_scale", "linear")

    cfg = ticks_to_calibration_config(ticks, axes, x_scale, y_scale)

    if not cfg:
        return {
            "suggested_calibration_config": None,
            "auto_confidence": 0.0,
            "calibration_diagnostics": None,
            "axis_geometry": axes,
            "ticks": ticks,
            "source": source,
            "auto_calibration_applied": False,
        }

    auto_conf = cfg.pop("auto_confidence", 0.0)
    diagnostics = cfg.pop("calibration_diagnostics", None)

    return {
        "suggested_calibration_config": cfg,
        "auto_confidence": auto_conf,
        "calibration_diagnostics": diagnostics,
        "axis_geometry": axes,
        "ticks": ticks,
        "scale_detection": scale_info,
        "source": source,
        "auto_calibration_applied": auto_conf >= 0.65,
    }
