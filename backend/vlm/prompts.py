CLASSIFY_PROMPT = """你是科研图表分析专家。请判断这张图表的类型。
只能从以下选项中选择一个，仅输出类型的英文单词，不要任何解释：
line, scatter, bar, heatmap, box, pie, contour, microscopy, unknown

类型说明：
- line: 折线图
- scatter: 散点图
- bar: 柱状图/条形图
- heatmap: 热图/矩阵图
- box: 箱线图
- pie: 饼图
- contour: 等高线图
- microscopy: 显微镜图像/实验照片
- unknown: 无法归类

只输出一个单词："""


SEMANTICS_PROMPT = """你是科研图表分析专家。请仔细观察这张图表，
提取以下语义信息，以严格的 JSON 格式输出（不要 markdown 代码块标记）：

{
  "title": "图表标题，无则 null",
  "x_label": "X轴完整标签文字（可含单位），无则 null",
  "y_label": "Y轴完整标签文字（可含单位），无则 null",
  "x_quantity": "X轴物理量名称（不含单位），无则 null",
  "y_quantity": "Y轴物理量名称（不含单位），无则 null",
  "x_unit": "X轴单位，无则 null",
  "y_unit": "Y轴单位，无则 null",
  "x_scale": "linear 或 log",
  "y_scale": "linear 或 log",
  "legend": ["图例项1", "图例项2"],
  "series_colors": {"图例项1": "#hex颜色"},
  "data_range_hint": {
    "x_min": null, "x_max": null,
    "y_min": null, "y_max": null
  },
  "notes": "其他重要观察"
}

【重要约束】：
- 你只负责理解语义和文字，绝对不要臆测或编造具体数据点的数值坐标。
- 数据点的精确数值将由专门的算法提取。
- x_quantity/y_quantity 与 x_unit/y_unit 应分开填写；若无法拆分则 quantity 填主要物理量名。

直接输出 JSON："""


REGION_SEGMENT_PROMPT = """你是科研图表版面分析专家。请识别图中各功能区域的边界框。
以严格 JSON 输出（不要 markdown 代码块），坐标使用像素，原点在图像左上角：

{
  "coord_space": "pixel",
  "image_width": 图像宽度像素,
  "image_height": 图像高度像素,
  "regions": [
    {
      "kind": "plot_area | legend | legend_marker | x_axis | y_axis | x_tick_labels | y_tick_labels | title | colorbar | other_text",
      "bbox": {"x0": 左, "y0": 上, "x1": 右, "y1": 下},
      "label": "可选说明",
      "confidence": 0.0到1.0
    }
  ]
}

要求：
- plot_area 为数据曲线/点所在的主绘图区（不含外围刻度数字区域时可略含轴线）。
- legend 为图例框（含色块/线型与文字），务必准确框选，避免与曲线混淆。
- legend_marker 为图例中的小色块/线型样本（若与 legend 框分离可单独标注）。
- x_tick_labels / y_tick_labels 为刻度数字区域。
- title 为标题文字区域。
- 图例若在 plot_area 内部，legend 框必须完整覆盖图例文字和样本 marker，避免 marker 被误认为数据点。
- 不要输出数据点坐标，只输出区域框。

直接输出 JSON："""


AXIS_TICKS_PROMPT = """你是科研图表坐标轴分析专家。请读取图中 X/Y 轴刻度数字及其在图中的位置。
以严格 JSON 输出（不要 markdown）：

{
  "coord_space": "normalized",
  "image_width": 图像宽度像素,
  "image_height": 图像高度像素,
  "x_scale": "linear 或 log",
  "y_scale": "linear 或 log",
  "x_tick_format": "图中X轴刻度书写格式示例，如 10^n 或 1e-3",
  "y_tick_format": "图中Y轴刻度书写格式示例",
  "x_ticks": [
    {
      "value": 数值（真实数值，非像素）,
      "label_text": "图中该刻度原样文字，如 10^{-2} 或 1e-3 或 10^26",
      "position": {"x": 0.0-1.0, "y": 0.0-1.0}
    }
  ],
  "y_ticks": [ ... ]
}

要求：
- position 为刻度数字标签中心在图中的归一化坐标（相对整图宽高的 0~1）。
- label_text 必须与图中刻度标签一致（含上标、科学计数法、乘号等），value 为解析后的真实数值。
- 大数量级必须用科学计数法理解（如 10^26 对应 value=1e26），不要输出未缩放的巨大整数除非图中如此印刷。
- 对数轴刻度 value 必须为正数；按图中坐标轴实际格式读数。
- 只列出能清楚读到的主刻度，不要臆造数据点。
- 尽量每轴至少 2 个、至多 8 个刻度。

直接输出 JSON："""


CASES_PROMPT = """你是科研图表数据系列分析专家。图中可能同时包含多种数据表示（如实线理论曲线、虚线、散点仿真点、误差带等）。
请根据图例、颜色、线型识别每个应单独提取的数据系列（case）。
以严格 JSON 输出（不要 markdown）：

{
  "cases": [
    {
      "label": "图例名称",
      "color_hex": "#RRGGBB",
      "representation": "line | scatter | band",
      "sub_bbox": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
      "notes": "可选：线型/点型说明"
    }
  ]
}

要求：
- sub_bbox 为归一化坐标 0~1，限定该系列主要出现的区域（通常为 plot_area 内子区，可省略则全图）。
- line=连续折线/理论曲线；scatter=离散点；band=阴影误差带/置信区间。
- 每个图例项对应一个 case；颜色取图中该系列主色。
- 不要合并不同图例项为一个 case。

直接输出 JSON："""


def build_point_audit_prompt(
    detected_summary: str,
    regions_summary: str,
    semantics_summary: str,
) -> str:
    return f"""你是科研图表数据审核专家。CV 算法已从图中提取候选数据点（像素坐标）。
请对照原图判断哪些点是误识别（如图例标记、文字、坐标轴、标题、色条等非数据元素）。

【区域信息】
{regions_summary}

【语义信息】
{semantics_summary}

【CV 检测点（series_idx, point_idx, pixel_x, pixel_y, series_name, color）】
{detected_summary}

以严格 JSON 输出（不要 markdown）：
{{
  "removals": [
    {{
      "series_idx": 0,
      "point_idx": 0,
      "pixel_x": 123.0,
      "pixel_y": 456.0,
      "reason": "位于图例区域",
      "confidence": 0.95
    }}
  ],
  "notes": "可选说明"
}}

只列出应剔除的误识别点；真实数据点不要列入。若无误识别则 removals 为空数组。
直接输出 JSON："""
