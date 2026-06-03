import json
from pathlib import Path

from config import RESULTS_DIR
from core.schemas import ExtractionResult


def save_result(image_id: str, result: ExtractionResult, calibration: dict | None = None):
    payload = {
        "result": result.model_dump(mode="json"),
        "calibration": calibration,
    }
    path = RESULTS_DIR / f"{image_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_result(image_id: str) -> ExtractionResult | None:
    path = RESULTS_DIR / f"{image_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return ExtractionResult.model_validate(data["result"])
