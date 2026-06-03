"""本地 Qwen2-VL — 需额外安装 torch/transformers，见附录 B。"""

import io

import numpy as np
from PIL import Image

from core.schemas import ChartType
from vlm.parser import parse_json_response
from vlm.prompts import (
    CLASSIFY_PROMPT,
    REGION_SEGMENT_PROMPT,
    SEMANTICS_PROMPT,
    build_point_audit_prompt,
)
from vlm.provider import VLMProvider


class LocalQwenProvider(VLMProvider):
    def __init__(self, model_path: str | None = None):
        import os
        import torch
        from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

        path = model_path or os.getenv("QWEN_VL_MODEL_PATH", "/app/models/qwen2-vl")
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            path, torch_dtype=torch.float16, device_map="auto"
        )
        self.processor = AutoProcessor.from_pretrained(path)

    def _run(self, image: Image.Image, prompt: str) -> str:
        messages = [
            {
                "role": "user",
                "content": [{"type": "image"}, {"type": "text", "text": prompt}],
            }
        ]
        text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image], return_tensors="pt").to(
            self.model.device
        )
        out = self.model.generate(**inputs, max_new_tokens=1000, do_sample=False)
        result = self.processor.batch_decode(
            out[:, inputs.input_ids.shape[1] :], skip_special_tokens=True
        )[0]
        return result

    async def classify_chart_type(self, img: np.ndarray) -> ChartType:
        pil = Image.fromarray(img)
        text = self._run(pil, CLASSIFY_PROMPT).strip().lower()
        try:
            return ChartType(text.split()[0])
        except ValueError:
            return ChartType.UNKNOWN

    async def analyze_semantics(self, image_bytes: bytes) -> dict:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = self._run(pil, SEMANTICS_PROMPT)
        return parse_json_response(text)

    async def segment_regions(self, image_bytes: bytes) -> dict:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = self._run(pil, REGION_SEGMENT_PROMPT)
        return parse_json_response(text)

    async def audit_points(
        self,
        image_bytes: bytes,
        detected_summary: str,
        regions_summary: str,
        semantics_summary: str,
    ) -> dict:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        prompt = build_point_audit_prompt(
            detected_summary, regions_summary, semantics_summary
        )
        text = self._run(pil, prompt)
        return parse_json_response(text)
