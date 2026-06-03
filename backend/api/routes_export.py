import io
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.schemas import ExtractionResult
from config import UPLOAD_DIR
from export.exporters import export_csv, export_excel, export_json
from export.report import generate_report
from storage.results import load_result

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportBody(BaseModel):
    series: list[Any] | None = None
    result: dict | None = None


def _result_from_body(image_id: str, body: ExportBody | None) -> ExtractionResult:
    if body and body.result:
        return ExtractionResult.model_validate(body.result)
    if body and body.series:
        from core.schemas import ChartType, DataSeries, Point

        series = []
        for s in body.series:
            pts = [Point(**p) if isinstance(p, dict) else Point(x=p["x"], y=p["y"]) for p in s.get("points", [])]
            series.append(
                DataSeries(
                    name=s.get("name", "series"),
                    color_hex=s.get("color_hex"),
                    points=pts,
                    confidence=s.get("confidence", 1.0),
                )
            )
        return ExtractionResult(chart_type=ChartType.LINE, series=series)

    stored = load_result(image_id)
    if not stored:
        raise HTTPException(404, "未找到提取结果，请先执行提取")
    return stored


@router.get("/{image_id}")
async def export_get(image_id: str, format: str = Query("csv")):
    result = load_result(image_id)
    if not result:
        raise HTTPException(404, "未找到提取结果")
    return _stream_export(result, format, image_id)


@router.post("/{image_id}")
async def export_post(
    image_id: str,
    format: str = Query("csv"),
    body: ExportBody | None = None,
):
    result = _result_from_body(image_id, body)
    return _stream_export(result, format, image_id)


def _stream_export(result: ExtractionResult, format: str, image_id: str | None = None):
    if format == "csv":
        data, mime, fn = export_csv(result), "text/csv", "data.csv"
    elif format == "excel":
        data, mime, fn = export_excel(result), (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ), "data.xlsx"
    elif format == "json":
        data, mime, fn = export_json(result), "application/json", "data.json"
    elif format == "pdf":
        if not image_id:
            raise HTTPException(400, "PDF 导出需要 image_id")
        img_path = UPLOAD_DIR / image_id
        if not img_path.exists():
            raise HTTPException(404, "原图不存在")
        data = generate_report(result, img_path.read_bytes())
        mime, fn = "application/pdf", "report.pdf"
    else:
        raise HTTPException(400, "不支持的格式")

    return StreamingResponse(
        io.BytesIO(data),
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )
