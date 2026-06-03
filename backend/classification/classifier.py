from classification.rules import rule_based_hint
from core.schemas import ChartType


async def classify_chart(img, vlm) -> ChartType:
    rule_hint = rule_based_hint(img)
    vlm_type = await vlm.classify_chart_type(img)
    return vlm_type or rule_hint or ChartType.UNKNOWN
