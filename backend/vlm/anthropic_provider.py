import base64
import os

import cv2
import numpy as np

from core.schemas import ChartType
from vlm.parser import parse_json_response
from vlm.prompts import (
    CLASSIFY_PROMPT,
    REGION_SEGMENT_PROMPT,
    SEMANTICS_PROMPT,
    build_point_audit_prompt,
)
from vlm.provider import VLMProvider


class AnthropicProvider(VLMProvider):
    def __init__(self, model: str | None = None):
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model or os.getenv("ANTHROPIC_VLM_MODEL", "claude-3-5-sonnet-20241022")

    def _encode_ndarray(self, img: np.ndarray) -> tuple[str, bytes]:
        _, buf = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        return "image/png", buf.tobytes()

    async def _ask(self, media_type: str, data: bytes, prompt: str) -> str:
        b64 = base64.standard_b64encode(data).decode()
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        parts = [b.text for b in resp.content if hasattr(b, "text")]
        return "".join(parts)

    async def classify_chart_type(self, img: np.ndarray) -> ChartType:
        media_type, data = self._encode_ndarray(img)
        text = (await self._ask(media_type, data, CLASSIFY_PROMPT)).strip().lower()
        try:
            return ChartType(text.split()[0])
        except ValueError:
            return ChartType.UNKNOWN

    async def analyze_semantics(self, image_bytes: bytes) -> dict:
        from preprocessing.loader import load_image

        arr = load_image(image_bytes)
        media_type, data = self._encode_ndarray(arr)
        text = await self._ask(media_type, data, SEMANTICS_PROMPT)
        return parse_json_response(text)

    async def segment_regions(self, image_bytes: bytes) -> dict:
        from preprocessing.loader import load_image

        arr = load_image(image_bytes)
        media_type, data = self._encode_ndarray(arr)
        text = await self._ask(media_type, data, REGION_SEGMENT_PROMPT)
        return parse_json_response(text)

    async def audit_points(
        self,
        image_bytes: bytes,
        detected_summary: str,
        regions_summary: str,
        semantics_summary: str,
    ) -> dict:
        from preprocessing.loader import load_image

        arr = load_image(image_bytes)
        media_type, data = self._encode_ndarray(arr)
        prompt = build_point_audit_prompt(
            detected_summary, regions_summary, semantics_summary
        )
        text = await self._ask(media_type, data, prompt)
        return parse_json_response(text)
