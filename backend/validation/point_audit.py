"""VLM point-level audit helpers."""

from __future__ import annotations

import json

from core.schemas import DataSeries, PlotRegions, PointRemovalSuggestion


def format_detected_summary(series: list[DataSeries], detected_pixels: dict[str, list[dict]]) -> str:
    lines: list[str] = []
    for si, s in enumerate(series):
        pixels = detected_pixels.get(s.color_hex or "", [])
        if not pixels and s.points:
            for pi, _ in enumerate(s.points):
                lines.append(
                    f"{si},{pi},?,?,\"{s.name}\",{s.color_hex or ''}"
                )
            continue
        for pi, p in enumerate(pixels):
            lines.append(
                f'{si},{pi},{p.get("x", 0):.1f},{p.get("y", 0):.1f},"{s.name}",{s.color_hex or ""}'
            )
    return "\n".join(lines[:500]) or "(no points)"


def format_regions_summary(regions: PlotRegions | None) -> str:
    if not regions or not regions.regions:
        return "(no regions)"
    parts = []
    for r in regions.regions:
        b = r.bbox
        parts.append(
            f"{r.kind}: ({b.x0},{b.y0})-({b.x1},{b.y1}) conf={b.confidence:.2f}"
        )
    return "\n".join(parts)


def format_semantics_summary(semantics: dict) -> str:
    subset = {
        k: semantics.get(k)
        for k in (
            "title",
            "x_label",
            "y_label",
            "x_quantity",
            "y_quantity",
            "x_unit",
            "y_unit",
            "legend",
            "notes",
        )
    }
    return json.dumps(subset, ensure_ascii=False)


def parse_audit_removals(raw: dict) -> list[PointRemovalSuggestion]:
    out: list[PointRemovalSuggestion] = []
    for item in raw.get("removals", []) or []:
        if not isinstance(item, dict):
            continue
        try:
            out.append(
                PointRemovalSuggestion(
                    series_idx=int(item["series_idx"]),
                    point_idx=int(item["point_idx"]),
                    pixel_x=float(item.get("pixel_x", 0)),
                    pixel_y=float(item.get("pixel_y", 0)),
                    reason=str(item.get("reason", "misdetected")),
                    confidence=float(item.get("confidence", 0.8)),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return out
