import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import UPLOAD_DIR, safe_child_path
from preprocessing.pdf_loader import is_pdf, list_pdf_pages, pdf_page_to_png

router = APIRouter(prefix="/api/projects", tags=["projects"])


class PdfPageRequest(BaseModel):
    source_id: str
    page: int = 0
    dpi: int = 200


def _png_id_from_pdf(source_id: str, page: int) -> str:
    base = Path(source_id).stem
    return f"{base}_p{page}.png"


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    filename = Path(file.filename or "image").name
    content = await file.read()
    uid = str(uuid.uuid4())
    source_type = "image"

    if is_pdf(content, filename):
        source_type = "pdf"
        pdf_id = f"{uid}_{filename}"
        pdf_path = safe_child_path(UPLOAD_DIR, pdf_id)
        pdf_path.write_bytes(content)
        pages = list_pdf_pages(content)
        page_index = 0
        png_bytes = pdf_page_to_png(content, page_index)
        image_id = _png_id_from_pdf(pdf_id, page_index)
        png_path = safe_child_path(UPLOAD_DIR, image_id)
        png_path.write_bytes(png_bytes)
        return {
            "image_id": image_id,
            "url": f"/api/projects/image/{image_id}",
            "source_type": source_type,
            "source_id": pdf_id,
            "selected_page": page_index,
            "pages": pages,
        }

    image_id = f"{uid}_{filename}"
    path = safe_child_path(UPLOAD_DIR, image_id)
    path.write_bytes(content)
    return {
        "image_id": image_id,
        "url": f"/api/projects/image/{image_id}",
        "source_type": source_type,
        "source_id": image_id,
        "selected_page": 0,
        "pages": [],
    }


@router.post("/pdf-page")
async def select_pdf_page(req: PdfPageRequest):
    try:
        pdf_path = safe_child_path(UPLOAD_DIR, req.source_id)
    except ValueError as exc:
        raise HTTPException(400, "非法 PDF 路径") from exc
    if not pdf_path.exists():
        raise HTTPException(404, "PDF 不存在")
    content = pdf_path.read_bytes()
    if not is_pdf(content):
        raise HTTPException(400, "源文件不是 PDF")
    pages = list_pdf_pages(content)
    if req.page < 0 or req.page >= len(pages):
        raise HTTPException(400, "页码超出范围")
    png_bytes = pdf_page_to_png(content, req.page, dpi=req.dpi)
    image_id = _png_id_from_pdf(req.source_id, req.page)
    png_path = safe_child_path(UPLOAD_DIR, image_id)
    png_path.write_bytes(png_bytes)
    return {
        "image_id": image_id,
        "url": f"/api/projects/image/{image_id}",
        "source_type": "pdf",
        "source_id": req.source_id,
        "selected_page": req.page,
        "pages": pages,
    }


@router.get("/image/{image_id}")
async def get_image(image_id: str):
    try:
        path = safe_child_path(UPLOAD_DIR, image_id)
    except ValueError:
        raise HTTPException(400, "非法图片路径")
    if not path.exists():
        raise HTTPException(404, "图片不存在")
    return FileResponse(path)
