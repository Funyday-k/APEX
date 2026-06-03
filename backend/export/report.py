import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.schemas import ExtractionResult


def generate_report(result: ExtractionResult, original_img_bytes: bytes) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("科研图表提取报告", styles["Title"]))
    elements.append(Spacer(1, 12))

    x_axis = result.x_label or "-"
    if result.x_quantity or result.x_unit:
        x_axis = f"{result.x_quantity or ''} ({result.x_unit or ''})".strip()
    y_axis = result.y_label or "-"
    if result.y_quantity or result.y_unit:
        y_axis = f"{result.y_quantity or ''} ({result.y_unit or ''})".strip()

    meta = [
        ["图表类型", result.chart_type.value],
        ["标题", result.title or "-"],
        ["X轴", x_axis],
        ["Y轴", y_axis],
        ["整体置信度", f"{result.overall_confidence:.2%}"],
        ["系列数量", str(len(result.series))],
    ]
    if result.suggested_removals:
        meta.append(["AI 建议剔除点数", str(len(result.suggested_removals))])
    t = Table(meta, colWidths=[120, 350])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("原始图表", styles["Heading2"]))
    elements.append(RLImage(io.BytesIO(original_img_bytes), width=400, height=300))
    elements.append(Spacer(1, 12))

    if result.low_confidence_flags:
        elements.append(Paragraph("需人工复核项", styles["Heading2"]))
        for flag in result.low_confidence_flags:
            elements.append(Paragraph(f"• {flag}", styles["Normal"]))

    doc.build(elements)
    return buf.getvalue()
