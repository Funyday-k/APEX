import io
import json

import pandas as pd

from core.schemas import ExtractionResult


def to_dataframe(result: ExtractionResult) -> pd.DataFrame:
    rows = []
    for s in result.series:
        for p in s.points:
            rows.append(
                {
                    "series": s.name,
                    "x": p.x,
                    "y": p.y,
                    "confidence": s.confidence,
                }
            )
    return pd.DataFrame(rows)


def export_csv(result: ExtractionResult) -> bytes:
    return to_dataframe(result).to_csv(index=False).encode("utf-8-sig")


def export_json(result: ExtractionResult) -> bytes:
    return result.model_dump_json(indent=2).encode("utf-8")


def export_excel(result: ExtractionResult) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for s in result.series:
            df = pd.DataFrame([{"x": p.x, "y": p.y} for p in s.points])
            sheet = (s.name[:31] or "series").replace("/", "_")
            df.to_excel(writer, sheet_name=sheet, index=False)
    return buf.getvalue()
