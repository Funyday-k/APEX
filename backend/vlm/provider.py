import os
from abc import ABC, abstractmethod

import numpy as np

from core.schemas import ChartType


class VLMProvider(ABC):
    @abstractmethod
    async def classify_chart_type(self, img: np.ndarray) -> ChartType | None: ...

    @abstractmethod
    async def analyze_semantics(self, image_bytes: bytes) -> dict: ...

    async def segment_regions(self, image_bytes: bytes) -> dict:
        """Return raw VLM JSON for plot regions; empty dict if unsupported."""
        return {}

    async def audit_points(
        self,
        image_bytes: bytes,
        detected_summary: str,
        regions_summary: str,
        semantics_summary: str,
    ) -> dict:
        """Return raw VLM JSON with removals list; empty dict if unsupported."""
        return {}

    async def evaluate_extraction(
        self,
        image_bytes: bytes,
        detected_summary: str,
        regions_summary: str,
        semantics_summary: str,
    ) -> dict:
        """Return quality evaluation JSON; empty dict if unsupported."""
        return {}

    async def read_axis_ticks(self, image_bytes: bytes) -> dict:
        """Return axis tick values and positions; empty dict if unsupported."""
        return {}

    async def detect_cases(self, image_bytes: bytes) -> dict:
        """Return composite series cases JSON; empty dict if unsupported."""
        return {}


class StubVLMProvider(VLMProvider):
    """无 API Key 或未配置 VLM 时使用。"""

    async def classify_chart_type(self, img: np.ndarray) -> ChartType | None:
        return None

    async def analyze_semantics(self, image_bytes: bytes) -> dict:
        return {}

    async def segment_regions(self, image_bytes: bytes) -> dict:
        return {}

    async def audit_points(
        self,
        image_bytes: bytes,
        detected_summary: str,
        regions_summary: str,
        semantics_summary: str,
    ) -> dict:
        return {}

    async def evaluate_extraction(
        self,
        image_bytes: bytes,
        detected_summary: str,
        regions_summary: str,
        semantics_summary: str,
    ) -> dict:
        return {}


def get_vlm_provider() -> VLMProvider:
    name = os.getenv("VLM_PROVIDER", "stub").lower()

    if name == "stub":
        return StubVLMProvider()

    if name == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            return StubVLMProvider()
        from vlm.openai_provider import OpenAIProvider

        return OpenAIProvider()

    if name == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            return StubVLMProvider()
        from vlm.anthropic_provider import AnthropicProvider

        return AnthropicProvider()

    if name == "local":
        try:
            from vlm.local_qwen import LocalQwenProvider

            return LocalQwenProvider()
        except ImportError:
            raise RuntimeError(
                "本地 VLM 需要 transformers/torch，见 DOC/appendix/B-local-vlm.md"
            ) from None

    raise ValueError(f"未知的 VLM_PROVIDER: {name}")
