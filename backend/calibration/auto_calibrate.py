"""Build calibration reference points from detected ticks."""

from __future__ import annotations

import math


def _pick_endpoint_ticks(ticks: list[dict]) -> tuple[dict, dict] | None:
    if len(ticks) < 2:
        return None
    sorted_ticks = sorted(ticks, key=lambda t: t["pixel"])
    return sorted_ticks[0], sorted_ticks[-1]


def ticks_to_calibration_config(
    ticks: dict,
    axis_geometry: dict,
    x_scale: str = "linear",
    y_scale: str = "linear",
) -> dict | None:
    """
    Return CalibrationConfig-compatible dict with ref1/ref2 per axis,
    or None if insufficient ticks.
    """
    xt = ticks.get("x_ticks") or []
    yt = ticks.get("y_ticks") or []
    x_pair = _pick_endpoint_ticks(xt)
    y_pair = _pick_endpoint_ticks(yt)
    if not x_pair or not y_pair:
        return None

    x_axis = axis_geometry.get("x_axis") or {}
    y_axis = axis_geometry.get("y_axis") or {}
    x_axis_y = int(x_axis.get("y_pixel", 0))
    y_axis_x = int(y_axis.get("x_pixel", 0))

    def _valid_log_value(v: float, scale: str) -> bool:
        if scale != "log":
            return True
        return v > 0

    t0, t1 = x_pair
    if not _valid_log_value(t0["value"], x_scale) or not _valid_log_value(t1["value"], x_scale):
        return None
    u0, u1 = y_pair
    if not _valid_log_value(u0["value"], y_scale) or not _valid_log_value(u1["value"], y_scale):
        return None

    return {
        "x_axis": {
            "scale": x_scale,
            "ref1": {
                "pixel": {"x": int(t0["pixel"]), "y": x_axis_y},
                "data": {"x": float(t0["value"]), "y": 0.0},
            },
            "ref2": {
                "pixel": {"x": int(t1["pixel"]), "y": x_axis_y},
                "data": {"x": float(t1["value"]), "y": 0.0},
            },
        },
        "y_axis": {
            "scale": y_scale,
            "ref1": {
                "pixel": {"x": y_axis_x, "y": int(u0["pixel"])},
                "data": {"x": 0.0, "y": float(u0["value"])},
            },
            "ref2": {
                "pixel": {"x": y_axis_x, "y": int(u1["pixel"])},
                "data": {"x": 0.0, "y": float(u1["value"])},
            },
        },
        "auto_confidence": _auto_calib_confidence(xt, yt, x_scale, y_scale),
    }


def _auto_calib_confidence(
    xt: list[dict], yt: list[dict], x_scale: str, y_scale: str
) -> float:
    score = 0.4
    if len(xt) >= 2:
        score += 0.25
    if len(yt) >= 2:
        score += 0.25
    if len(xt) >= 3:
        score += 0.05
    if len(yt) >= 3:
        score += 0.05
    for t in xt + yt:
        if t.get("value") is None or (isinstance(t["value"], float) and math.isnan(t["value"])):
            score -= 0.15
            break
    if x_scale == "log" or y_scale == "log":
        score -= 0.05
    return max(0.0, min(1.0, score))
