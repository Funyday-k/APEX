"""Tests for PDF rasterization."""

import io

import fitz
import numpy as np
from PIL import Image

from preprocessing.pdf_loader import is_pdf, list_pdf_pages, pdf_page_count, pdf_page_to_png


def _make_sample_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.insert_text((20, 50), "test chart")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def test_is_pdf():
    content = _make_sample_pdf()
    assert is_pdf(content)
    assert is_pdf(b"%PDF-1.4 junk", "chart.pdf")
    assert not is_pdf(b"\x89PNG\r\n")


def test_pdf_page_count_and_list():
    content = _make_sample_pdf()
    assert pdf_page_count(content) == 1
    pages = list_pdf_pages(content)
    assert len(pages) == 1
    assert pages[0]["page"] == 0


def test_pdf_page_to_png():
    content = _make_sample_pdf()
    png = pdf_page_to_png(content, 0, dpi=150)
    assert png[:4] == b"\x89PNG"
    img = Image.open(io.BytesIO(png))
    assert img.width > 100
    assert img.height > 50
