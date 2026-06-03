from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import UPLOAD_DIR, safe_child_path
from core.orchestrator import Orchestrator, enrich_series_for_api
from core.schemas import CalibrationConfig, ChartType, HeatmapOptions
from storage.results import save_result

router = APIRouter(prefix="/api/extract", tags=["extract"])
orchestrator = Orchestrator()


class AnalyzeRequest(BaseModel):
    image_id: str


class ExtractRequest(BaseModel):
    image_id: str
    chart_type: ChartType
    calibration: CalibrationConfig
    series_colors: list[str] | None = None
    heatmap_options: HeatmapOptions | None = None
    semantics: dict | None = None
    regions: dict | None = None


def _load_bytes(image_id: str) -> bytes:
    try:
        path = safe_child_path(UPLOAD_DIR, image_id)
    except ValueError as exc:
        raise HTTPException(400, "非法图片路径") from exc
    if not path.exists():
        raise HTTPException(404, "图片不存在")
    return path.read_bytes()


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    image_bytes = _load_bytes(req.image_id)
    return await orchestrator.auto_analyze(image_bytes)


@router.post("/run")
async def run_extraction(req: ExtractRequest):
    image_bytes = _load_bytes(req.image_id)
    try:
        result = await orchestrator.extract(
            image_bytes,
            req.chart_type,
            req.calibration,
            req.series_colors,
            req.heatmap_options,
            semantics=req.semantics,
            regions=req.regions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    save_result(
        req.image_id,
        result,
        calibration=req.calibration.model_dump(mode="json"),
    )
    return enrich_series_for_api(result, req.calibration)
