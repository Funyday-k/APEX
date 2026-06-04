from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import UPLOAD_DIR, safe_child_path
from core.orchestrator import Orchestrator, enrich_series_for_api
from core.schemas import CalibrationConfig, ChartType, HeatmapOptions
from storage.results import save_result

router = APIRouter(prefix="/api/extract", tags=["extract"])
orchestrator = Orchestrator()


class AnalyzeOptions(BaseModel):
    chart_type_override: str | None = None
    use_vlm_regions: bool = True
    force_redetect_plot: bool = False


class AnalyzeRequest(BaseModel):
    image_id: str
    options: AnalyzeOptions | None = None


class ExtractOptions(BaseModel):
    color_tolerance: int | None = Field(default=None, ge=1, le=80)
    min_marker_area: int | None = Field(default=None, ge=1, le=500)
    suppress_grid: bool | None = None
    intersect_auto: bool | None = None
    enable_vlm_audit: bool = True
    enable_ai_evaluation: bool = True


class ExtractRequest(BaseModel):
    image_id: str
    chart_type: ChartType
    calibration: CalibrationConfig
    series_colors: list[str] | None = None
    heatmap_options: HeatmapOptions | None = None
    semantics: dict | None = None
    regions: dict | None = None
    extract_options: ExtractOptions | None = None


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
    opts = req.options or AnalyzeOptions()
    return await orchestrator.auto_analyze(
        image_bytes,
        chart_type_override=opts.chart_type_override,
        use_vlm_regions=opts.use_vlm_regions,
        force_redetect_plot=opts.force_redetect_plot,
    )


@router.post("/run")
async def run_extraction(req: ExtractRequest):
    image_bytes = _load_bytes(req.image_id)
    extract_kw: dict = {}
    if req.extract_options:
        extract_kw = req.extract_options.model_dump(exclude_none=True)
    try:
        result = await orchestrator.extract(
            image_bytes,
            req.chart_type,
            req.calibration,
            req.series_colors,
            req.heatmap_options,
            semantics=req.semantics,
            regions=req.regions,
            extract_options=extract_kw,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    save_result(
        req.image_id,
        result,
        calibration=req.calibration.model_dump(mode="json"),
    )
    out = enrich_series_for_api(result, req.calibration)
    out["ai_evaluation_score"] = result.metadata.get("ai_evaluation_score")
    return out
