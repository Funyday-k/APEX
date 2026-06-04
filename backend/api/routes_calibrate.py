from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from calibration.ai_calibrate import ai_auto_calibrate
from calibration.calibrator import Calibrator
from config import UPLOAD_DIR, safe_child_path
from core.schemas import CalibrationConfig

router = APIRouter(prefix="/api/calibrate", tags=["calibrate"])


class RecomputeRequest(BaseModel):
    calibration: CalibrationConfig
    pixel_points: list[dict]


class AutoCalibrateRequest(BaseModel):
    image_id: str
    use_vlm: bool = True


def _load_bytes(image_id: str) -> bytes:
    try:
        path = safe_child_path(UPLOAD_DIR, image_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="非法图片路径") from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    return path.read_bytes()


@router.post("/auto")
async def auto_calibrate(req: AutoCalibrateRequest):
    image_bytes = _load_bytes(req.image_id)
    return await ai_auto_calibrate(image_bytes, use_vlm=req.use_vlm)


@router.post("/recompute")
async def recompute(req: RecomputeRequest):
    try:
        calibrator = Calibrator(req.calibration)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    results = []
    for item in req.pixel_points:
        try:
            data_pt = calibrator.pixel_to_data(item["px"], item["py"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="无效的像素点参数") from exc
        results.append(
            {
                "series_idx": item["series_idx"],
                "point_idx": item["point_idx"],
                "x": data_pt.x,
                "y": data_pt.y,
                "px": item["px"],
                "py": item["py"],
            }
        )
    return {"points": results}
