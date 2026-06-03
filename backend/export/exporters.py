import io
import json
import re

import pandas as pd

from core.schemas import ExtractionResult

INVALID_EXCEL_SHEET_CHARS = re.compile(r"[:\\/?*\[\]]")


def to_dataframe(result: ExtractionResult) -> pd.DataFrame:
    rows = []
    for s in result.series:
        for idx, p in enumerate(s.points):
            error = s.errors[idx] if idx < len(s.errors) else None
            row = {
                "series": s.name,
                "x": p.x,
                "y": p.y,
                "confidence": s.confidence,
            }
            if error is not None:
                row.update(
                    {
                        "y_err_upper": error.y_err_upper,
                        "y_err_lower": error.y_err_lower,
                        "x_err_left": error.x_err_left,
                        "x_err_right": error.x_err_right,
                    }
                )
            rows.append(row)
    return pd.DataFrame(rows)


def export_csv(result: ExtractionResult) -> bytes:
    return to_dataframe(result).to_csv(index=False).encode("utf-8-sig")


def export_json(result: ExtractionResult) -> bytes:
    return result.model_dump_json(indent=2).encode("utf-8")


def export_excel(result: ExtractionResult) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        used_sheet_names: set[str] = set()
        for idx, s in enumerate(result.series, start=1):
            rows = []
            for point_idx, p in enumerate(s.points):
                error = s.errors[point_idx] if point_idx < len(s.errors) else None
                row = {"x": p.x, "y": p.y}
                if error is not None:
                    row.update(
                        {
                            "y_err_upper": error.y_err_upper,
                            "y_err_lower": error.y_err_lower,
                            "x_err_left": error.x_err_left,
                            "x_err_right": error.x_err_right,
                        }
                    )
                rows.append(row)
            df = pd.DataFrame(rows)
            base_sheet = INVALID_EXCEL_SHEET_CHARS.sub("_", s.name).strip() or "series"
            sheet = base_sheet[:31]
            if sheet in used_sheet_names:
                suffix = f"_{idx}"
                sheet = f"{base_sheet[: 31 - len(suffix)]}{suffix}"
            used_sheet_names.add(sheet)
            df.to_excel(writer, sheet_name=sheet, index=False)
    return buf.getvalue()
