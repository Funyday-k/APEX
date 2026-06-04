"""PDF rasterization for chart extraction pipeline."""

from __future__ import annotations

import io

from PIL import Image


def is_pdf(content: bytes, filename: str | None = None) -> bool:
    if filename and filename.lower().endswith(".pdf"):
        return True
    return len(content) >= 4 and content[:4] == b"%PDF"


def pdf_page_count(content: bytes) -> int:
    import fitz

    doc = fitz.open(stream=content, filetype="pdf")
    try:
        return len(doc)
    finally:
        doc.close()


def list_pdf_pages(content: bytes) -> list[dict]:
    import fitz

    doc = fitz.open(stream=content, filetype="pdf")
    try:
        pages = []
        for i in range(len(doc)):
            rect = doc[i].rect
            pages.append(
                {
                    "page": i,
                    "width": int(rect.width),
                    "height": int(rect.height),
                }
            )
        return pages
    finally:
        doc.close()


def pdf_page_to_png(content: bytes, page_index: int = 0, dpi: int = 200) -> bytes:
    import fitz

    doc = fitz.open(stream=content, filetype="pdf")
    try:
        if page_index < 0 or page_index >= len(doc):
            raise ValueError(f"PDF page index out of range: {page_index}")
        page = doc[page_index]
        scale = dpi / 72.0
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def pdf_page_to_rgb_array(content: bytes, page_index: int = 0, dpi: int = 200):
    png_bytes = pdf_page_to_png(content, page_index, dpi=dpi)
    pil = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    import numpy as np

    return np.array(pil)
