import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from config import UPLOAD_DIR, safe_child_path

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    filename = Path(file.filename or "image").name
    image_id = f"{uuid.uuid4()}_{filename}"
    path = safe_child_path(UPLOAD_DIR, image_id)
    content = await file.read()
    path.write_bytes(content)
    return {
        "image_id": image_id,
        "url": f"/api/projects/image/{image_id}",
    }


@router.get("/image/{image_id}")
async def get_image(image_id: str):
    try:
        path = safe_child_path(UPLOAD_DIR, image_id)
    except ValueError:
        from fastapi import HTTPException

        raise HTTPException(400, "非法图片路径")
    if not path.exists():
        from fastapi import HTTPException

        raise HTTPException(404, "图片不存在")
    return FileResponse(path)
