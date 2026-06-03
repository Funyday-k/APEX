from fastapi import APIRouter
from pydantic import BaseModel

from calibration.calibrator import Calibrator
from core.schemas import CalibrationConfig

router = APIRouter(prefix="/api/calibrate", tags=["calibrate"])


class RecomputeRequest(BaseModel):
    calibration: CalibrationConfig
    pixel_points: list[dict]


@router.post("/recompute")
async def recompute(req: RecomputeRequest):
    calibrator = Calibrator(req.calibration)
    results = []
    for item in req.pixel_points:
        data_pt = calibrator.pixel_to_data(item["px"], item["py"])
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
