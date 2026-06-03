import base64
import os

import cv2
import numpy as np
from openai import AsyncOpenAI

from core.schemas import ChartType
from vlm.parser import parse_json_response
from vlm.prompts import (
    CLASSIFY_PROMPT,
    REGION_SEGMENT_PROMPT,
    SEMANTICS_PROMPT,
    build_point_audit_prompt,
)
from vlm.provider import VLMProvider


class OpenAIProvider(VLMProvider):
    def __init__(self, model: str | None = None):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**kwargs)
        self.model = model or os.getenv("OPENAI_VLM_MODEL", "gpt-4o")

    def _encode(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        return f"data:image/png;base64,{b64}"

    def _encode_ndarray(self, img: np.ndarray) -> str:
        _, buf = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        return self._encode(buf.tobytes())

    async def _ask(self, image_url: str, prompt: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url, "detail": "high"},
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=1000,
        )
        return resp.choices[0].message.content or ""

    async def classify_chart_type(self, img: np.ndarray) -> ChartType:
        url = self._encode_ndarray(img)
        text = (await self._ask(url, CLASSIFY_PROMPT)).strip().lower()
        try:
            return ChartType(text.split()[0])
        except ValueError:
            return ChartType.UNKNOWN

    async def analyze_semantics(self, image_bytes: bytes) -> dict:
        url = self._encode(image_bytes)
        text = await self._ask(url, SEMANTICS_PROMPT)
        return parse_json_response(text)

    async def segment_regions(self, image_bytes: bytes) -> dict:
        url = self._encode(image_bytes)
        text = await self._ask(url, REGION_SEGMENT_PROMPT)
        return parse_json_response(text)

    async def audit_points(
        self,
        image_bytes: bytes,
        detected_summary: str,
        regions_summary: str,
        semantics_summary: str,
    ) -> dict:
        url = self._encode(image_bytes)
        prompt = build_point_audit_prompt(
            detected_summary, regions_summary, semantics_summary
        )
        text = await self._ask(url, prompt)
        return parse_json_response(text)
