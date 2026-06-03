from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from calibration.calibrator import Calibrator
from core.schemas import CalibrationConfig

router = APIRouter(prefix="/api/calibrate", tags=["calibrate"])


class RecomputeRequest(BaseModel):
    calibration: CalibrationConfig
    pixel_points: list[dict]


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
