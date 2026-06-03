import os

import numpy as np


class OCREngine:
    """PaddleOCR；未安装或 OCR_ENABLED=0 时返回空列表。"""

    def __init__(self, lang: str = "ch"):
        self._ocr = None
        self._enabled = os.getenv("OCR_ENABLED", "1") != "0"
        self._lang = lang

    def _ensure(self):
        if self._ocr is not None or not self._enabled:
            return
        try:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(use_angle_cls=True, lang=self._lang, show_log=False)
        except Exception as e:
            print(f"[OCR] PaddleOCR 不可用，跳过: {e}")
            self._enabled = False

    def extract(self, img: np.ndarray) -> list[dict]:
        self._ensure()
        if not self._ocr:
            return []
        result = self._ocr.ocr(img, cls=True)
        items = []
        if not result or not result[0]:
            return items
        for line in result[0]:
            bbox, (text, conf) = line
            cx = float(np.mean([p[0] for p in bbox]))
            cy = float(np.mean([p[1] for p in bbox]))
            items.append(
                {
                    "text": text,
                    "center": (cx, cy),
                    "bbox": bbox,
                    "confidence": float(conf),
                }
            )
        return items
