"""Build calibration reference points from detected ticks via tick-model fitting."""

from __future__ import annotations

import math

import numpy as np


def _pick_endpoint_ticks(ticks: list[dict]) -> tuple[dict, dict] | None:
    if len(ticks) < 2:
        return None
    sorted_ticks = sorted(ticks, key=lambda t: t["pixel"])
    return sorted_ticks[0], sorted_ticks[-1]


def _filter_monotonic_inliers(ticks: list[dict], scale: str) -> list[dict]:
    """Drop outliers while keeping monotonic pixel order."""
    if len(ticks) < 3:
        return ticks
    sorted_ticks = sorted(ticks, key=lambda t: t["pixel"])
    pixels = np.array([float(t["pixel"]) for t in sorted_ticks], dtype=float)
    values = np.array([float(t["value"]) for t in sorted_ticks], dtype=float)
    if scale == "log" and np.any(values <= 0):
        return sorted_ticks
    target = np.log10(values) if scale == "log" else values
    A = np.vstack([pixels, np.ones(len(pixels))]).T
    coef, _, _, _ = np.linalg.lstsq(A, target, rcond=None)
    pred = A @ coef
    residuals = np.abs(target - pred)
    span = float(np.max(target) - np.min(target)) or 1.0
    thresh = max(1e-6, 0.12 * span)
    kept = [t for t, r in zip(sorted_ticks, residuals) if r <= thresh]
    return kept if len(kept) >= 2 else sorted_ticks


def _fit_axis_ticks(ticks: list[dict], scale: str) -> dict | None:
    """Fit pixel->value mapping; return ref pair and diagnostics."""
    if len(ticks) < 2:
        return None
    valid = [t for t in ticks if t.get("value") is not None and not _is_nan(t["value"])]
    if len(valid) < 2:
        return None
    valid = _filter_monotonic_inliers(valid, scale)
    if len(valid) < 2:
        return None

    pixels = np.array([float(t["pixel"]) for t in valid], dtype=float)
    values = np.array([float(t["value"]) for t in valid], dtype=float)
    order = np.argsort(pixels)
    pixels = pixels[order]
    values = values[order]

    if scale == "log":
        if np.any(values <= 0):
            return None
        target = np.log10(values)
    else:
        target = values

    # Linear fit: value = a * pixel + b
    A = np.vstack([pixels, np.ones(len(pixels))]).T
    coef, _, _, _ = np.linalg.lstsq(A, target, rcond=None)
    pred = A @ coef
    residuals = target - pred
    rms = float(np.sqrt(np.mean(residuals**2)))
    span = float(np.max(target) - np.min(target)) or 1.0
    rel_rms = rms / span

    endpoints = _pick_endpoint_ticks(valid)
    if not endpoints:
        return None
    t0, t1 = endpoints

    inlier_ratio = float(np.mean(np.abs(residuals) < max(1e-6, 0.08 * span)))
    confidence = _tick_fit_confidence(len(valid), rel_rms, inlier_ratio, scale)

    return {
        "ref1": t0,
        "ref2": t1,
        "rms": rms,
        "rel_rms": rel_rms,
        "inlier_ratio": inlier_ratio,
        "confidence": confidence,
        "n_ticks": len(valid),
    }


def _is_nan(v) -> bool:
    return isinstance(v, float) and math.isnan(v)


def _tick_fit_confidence(n: int, rel_rms: float, inlier_ratio: float, scale: str) -> float:
    score = 0.25
    if n >= 2:
        score += 0.2
    if n >= 3:
        score += 0.15
    if n >= 4:
        score += 0.1
    score += 0.25 * inlier_ratio
    score += max(0.0, 0.25 - rel_rms)
    if scale == "log":
        score -= 0.05
    return max(0.0, min(1.0, score))


def ticks_to_calibration_config(
    ticks: dict,
    axis_geometry: dict,
    x_scale: str = "linear",
    y_scale: str = "linear",
) -> dict | None:
    """
    Return CalibrationConfig-compatible dict with ref1/ref2 per axis,
    using tick-model fit confidence when multiple ticks are available.
    """
    xt = ticks.get("x_ticks") or []
    yt = ticks.get("y_ticks") or []
    x_fit = _fit_axis_ticks(xt, x_scale)
    y_fit = _fit_axis_ticks(yt, y_scale)
    if not x_fit or not y_fit:
        return None

    x_axis = axis_geometry.get("x_axis") or {}
    y_axis = axis_geometry.get("y_axis") or {}
    x_axis_y = int(x_axis.get("y_pixel", 0))
    y_axis_x = int(y_axis.get("x_pixel", 0))

    t0, t1 = x_fit["ref1"], x_fit["ref2"]
    u0, u1 = y_fit["ref1"], y_fit["ref2"]

    auto_conf = _auto_calib_confidence(x_fit, y_fit, x_scale, y_scale)

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
        "auto_confidence": auto_conf,
        "calibration_diagnostics": {
            "x": {
                "n_ticks": x_fit["n_ticks"],
                "rel_rms": x_fit["rel_rms"],
                "inlier_ratio": x_fit["inlier_ratio"],
                "confidence": x_fit["confidence"],
            },
            "y": {
                "n_ticks": y_fit["n_ticks"],
                "rel_rms": y_fit["rel_rms"],
                "inlier_ratio": y_fit["inlier_ratio"],
                "confidence": y_fit["confidence"],
            },
        },
    }


def _auto_calib_confidence(x_fit: dict, y_fit: dict, x_scale: str, y_scale: str) -> float:
    score = 0.35 * x_fit["confidence"] + 0.35 * y_fit["confidence"]
    if x_fit["n_ticks"] >= 3 and y_fit["n_ticks"] >= 3:
        score += 0.1
    if x_fit["rel_rms"] < 0.05 and y_fit["rel_rms"] < 0.05:
        score += 0.1
    if x_scale == "log" or y_scale == "log":
        score -= 0.03
    return max(0.0, min(1.0, score))
