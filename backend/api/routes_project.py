import uuid

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from config import UPLOAD_DIR

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    image_id = f"{uuid.uuid4()}_{file.filename}"
    path = UPLOAD_DIR / image_id
    content = await file.read()
    path.write_bytes(content)
    return {
        "image_id": image_id,
        "url": f"/api/projects/image/{image_id}",
    }


@router.get("/image/{image_id}")
async def get_image(image_id: str):
    path = UPLOAD_DIR / image_id
    if not path.exists():
        from fastapi import HTTPException

        raise HTTPException(404, "图片不存在")
    return FileResponse(path)
