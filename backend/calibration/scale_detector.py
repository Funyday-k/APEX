"""CV detection of linear vs logarithmic axis scale from tick positions."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np

ScaleType = Literal["linear", "log"]


def detect_axis_scale(
    ticks: list[dict],
    *,
    label_text: str | None = None,
    min_ticks: int = 3,
) -> tuple[ScaleType, float]:
    """
    Infer axis scale from tick pixel/value pairs.
    Returns (scale, confidence in [0, 1]).
    """
    if len(ticks) < 2:
        return "linear", 0.0

    label = (label_text or "").lower()
    if "log" in label and "linear" not in label:
        if _all_positive(ticks):
            return "log", 0.7

    if len(ticks) < min_ticks:
        return "linear", 0.35

    pixels = np.array([float(t["pixel"]) for t in ticks], dtype=float)
    values = np.array([float(t["value"]) for t in ticks], dtype=float)
    order = np.argsort(pixels)
    pixels = pixels[order]
    values = values[order]

    lin_rms = _fit_linear_rms(pixels, values)
    log_rms = float("inf")
    if _all_positive_values(values):
        log_rms = _fit_log_rms(pixels, values)

    if log_rms < lin_rms * 0.55 and log_rms < lin_rms - 1e-6:
        conf = min(0.95, 0.5 + (lin_rms - log_rms) / (lin_rms + 1e-6))
        return "log", conf

    if lin_rms < log_rms * 0.85 or not math.isfinite(log_rms):
        conf = min(0.95, 0.55 + min(0.35, (log_rms - lin_rms) / (log_rms + 1e-6)))
        return "linear", conf

    return "linear", 0.5


def infer_axis_scales(
    ticks: dict,
    *,
    x_label: str | None = None,
    y_label: str | None = None,
    vlm_x_scale: str | None = None,
    vlm_y_scale: str | None = None,
) -> dict:
    """Return CV scales with optional VLM override when CV is uncertain."""
    xt = ticks.get("x_ticks") or []
    yt = ticks.get("y_ticks") or []
    x_scale, x_conf = detect_axis_scale(xt, label_text=x_label)
    y_scale, y_conf = detect_axis_scale(yt, label_text=y_label)

    # Prefer CV when confident; VLM log only if CV agrees or CV has too few ticks
    if vlm_x_scale == "log" and x_scale == "linear" and x_conf >= 0.55:
        x_scale = "linear"
    elif vlm_x_scale == "log" and x_conf < 0.4 and len(xt) < 3:
        x_scale = "log"

    if vlm_y_scale == "log" and y_scale == "linear" and y_conf >= 0.55:
        y_scale = "linear"
    elif vlm_y_scale == "log" and y_conf < 0.4 and len(yt) < 3:
        y_scale = "log"

    return {
        "x_scale": x_scale,
        "y_scale": y_scale,
        "x_scale_confidence": x_conf,
        "y_scale_confidence": y_conf,
    }


def _all_positive(ticks: list[dict]) -> bool:
    return _all_positive_values([float(t["value"]) for t in ticks])


def _all_positive_values(values: np.ndarray) -> bool:
    return bool(np.all(values > 0))


def _fit_linear_rms(pixels: np.ndarray, values: np.ndarray) -> float:
    if len(pixels) < 2:
        return float("inf")
    A = np.vstack([pixels, np.ones(len(pixels))]).T
    coef, _, _, _ = np.linalg.lstsq(A, values, rcond=None)
    pred = A @ coef
    return float(np.sqrt(np.mean((pred - values) ** 2)))


def _fit_log_rms(pixels: np.ndarray, values: np.ndarray) -> float:
    if not _all_positive_values(values):
        return float("inf")
    log_v = np.log10(values)
    A = np.vstack([pixels, np.ones(len(pixels))]).T
    coef, _, _, _ = np.linalg.lstsq(A, log_v, rcond=None)
    pred = A @ coef
    return float(np.sqrt(np.mean((pred - log_v) ** 2)))
