"""Matplotlib-based synthetic chart images for regression tests."""

from __future__ import annotations

import io
from typing import Any

import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None  # type: ignore


def _require_plt():
    if plt is None:
        raise ImportError("matplotlib required for synthetic fixtures; pip install matplotlib")


def _fig_to_rgb(fig) -> np.ndarray:
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    rgb = buf[:, :, :3].copy()
    plt.close(fig)
    return rgb


def _rgb_to_png_bytes(rgb: np.ndarray) -> bytes:
    from PIL import Image

    img = Image.fromarray(rgb)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def calibration_from_axes(fig, ax, xscale: str = "linear", yscale: str = "linear") -> dict:
    """Build CalibrationConfig-compatible dict from matplotlib axes."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = ax.get_window_extent(renderer)
    x0, y0, x1, y1 = bbox.x0, bbox.y0, bbox.x1, bbox.y1
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_lo, x_hi = float(min(xlim)), float(max(xlim))
    y_lo, y_hi = float(min(ylim)), float(max(ylim))
    if xscale == "log":
        x_lo, x_hi = max(x_lo, 1e-6), max(x_hi, 1e-6)
    if yscale == "log":
        y_lo, y_hi = max(y_lo, 1e-6), max(y_hi, 1e-6)
    y_axis_x = float(x0)
    x_axis_y = float(y1)
    return {
        "x_axis": {
            "scale": xscale,
            "ref1": {
                "pixel": {"x": int(x0), "y": int(x_axis_y)},
                "data": {"x": x_lo, "y": 0.0},
            },
            "ref2": {
                "pixel": {"x": int(x1), "y": int(x_axis_y)},
                "data": {"x": x_hi, "y": 0.0},
            },
        },
        "y_axis": {
            "scale": yscale,
            "ref1": {
                "pixel": {"x": int(y_axis_x), "y": int(y1)},
                "data": {"x": 0.0, "y": y_lo},
            },
            "ref2": {
                "pixel": {"x": int(y_axis_x), "y": int(y0)},
                "data": {"x": 0.0, "y": y_hi},
            },
        },
    }


def _make_curve(xscale: str, yscale: str, seed: int, n: int = 40):
    rng = np.random.default_rng(seed)
    if xscale == "log":
        xs = np.logspace(-1, 1, n)
    else:
        xs = np.linspace(0, 10, n)
    ys = 2.0 + 0.3 * xs + rng.normal(0, 0.15, n)
    if yscale == "log":
        ys = np.clip(ys, 0.1, None)
    return xs, ys


def render_line_chart(
    *,
    xscale: str = "linear",
    yscale: str = "linear",
    legend_loc: str = "upper right",
    n_series: int = 2,
    seed: int = 0,
) -> tuple[np.ndarray, bytes, dict[str, Any]]:
    _require_plt()
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    truth: dict[str, Any] = {"series": [], "x_range": None, "y_range": None}
    for s in range(n_series):
        xs, ys = _make_curve(xscale, yscale, seed + s)
        ax.plot(xs, ys, label=f"series {s}", linewidth=2)
        truth["series"].append({"x": xs.tolist(), "y": ys.tolist()})
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    ax.legend(loc=legend_loc)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    cal = calibration_from_axes(fig, ax, xscale, yscale)
    rgb = _fig_to_rgb(fig)
    truth["calibration"] = cal
    truth["x_range"] = ax.get_xlim()
    truth["y_range"] = ax.get_ylim()
    truth["legend_loc"] = legend_loc
    return rgb, _rgb_to_png_bytes(rgb), truth


def render_scatter_with_error(
    *, seed: int = 0, n: int = 25
) -> tuple[np.ndarray, bytes, dict[str, Any]]:
    _require_plt()
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    xs = np.linspace(1, 10, n)
    ys = 2 * xs + rng.normal(0, 0.5, n)
    yerr = rng.uniform(0.2, 0.8, n)
    ax.errorbar(xs, ys, yerr=yerr, fmt="o", capsize=3, label="data")
    ax.legend(loc="upper left")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.tight_layout()
    cal = calibration_from_axes(fig, ax)
    rgb = _fig_to_rgb(fig)
    return rgb, _rgb_to_png_bytes(rgb), {"calibration": cal, "n_points": n}


def render_line_with_band(*, seed: int = 0) -> tuple[np.ndarray, bytes, dict[str, Any]]:
    _require_plt()
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    xs = np.linspace(0, 10, 50)
    mid = 3 + 0.4 * xs
    spread = 0.5 + 0.1 * xs
    ax.fill_between(xs, mid - spread, mid + spread, alpha=0.35, color="C0")
    ax.plot(xs, mid, color="C0", linewidth=2, label="fit")
    ax.legend()
    fig.tight_layout()
    cal = calibration_from_axes(fig, ax)
    rgb = _fig_to_rgb(fig)
    return rgb, _rgb_to_png_bytes(rgb), {"calibration": cal, "has_band": True}


def render_bar_chart(*, seed: int = 0) -> tuple[np.ndarray, bytes, dict[str, Any]]:
    _require_plt()
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    labels = ["A", "B", "C", "D", "E"]
    vals = rng.uniform(2, 8, len(labels))
    ax.bar(labels, vals, color="steelblue")
    ax.set_ylabel("value")
    fig.tight_layout()
    cal = calibration_from_axes(fig, ax)
    rgb = _fig_to_rgb(fig)
    return rgb, _rgb_to_png_bytes(rgb), {"calibration": cal, "n_bars": len(labels)}


def render_box_plot(*, seed: int = 0) -> tuple[np.ndarray, bytes, dict[str, Any]]:
    _require_plt()
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    data = [rng.normal(i, 1, 40) for i in range(4)]
    ax.boxplot(data, labels=["G1", "G2", "G3", "G4"])
    ax.set_ylabel("value")
    fig.tight_layout()
    cal = calibration_from_axes(fig, ax)
    rgb = _fig_to_rgb(fig)
    return rgb, _rgb_to_png_bytes(rgb), {"calibration": cal}


def render_heatmap(*, seed: int = 0) -> tuple[np.ndarray, bytes, dict[str, Any]]:
    _require_plt()
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(5.5, 4), dpi=100)
    data = rng.random((8, 10))
    im = ax.imshow(data, aspect="auto", cmap="viridis")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    cal = calibration_from_axes(fig, ax)
    rgb = _fig_to_rgb(fig)
    h, w = rgb.shape[:2]
    cbar_box = {"x0": int(w * 0.88), "y0": int(h * 0.15), "x1": w - 5, "y1": int(h * 0.85)}
    return rgb, _rgb_to_png_bytes(rgb), {
        "calibration": cal,
        "colorbar_box": cbar_box,
        "value_range": (float(data.min()), float(data.max())),
    }
