import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

DATA_DIR = Path(os.getenv("DATA_DIR", str(ROOT_DIR / "data")))
UPLOAD_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'sciplot.db'}")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def safe_child_path(directory: Path, name: str) -> Path:
    base = directory.resolve()
    path = (base / name).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError("非法文件路径") from exc
    return path
