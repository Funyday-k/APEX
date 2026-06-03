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
      "kind": "plot_area | legend | x_axis | y_axis | x_tick_labels | y_tick_labels | title | colorbar | other_text",
      "bbox": {"x0": 左, "y0": 上, "x1": 右, "y1": 下},
      "label": "可选说明",
      "confidence": 0.0到1.0
    }
  ]
}

要求：
- plot_area 为数据曲线/点所在的主绘图区（不含外围刻度数字区域时可略含轴线）。
- legend 为图例框（含色块/线型与文字），务必准确框选，避免与曲线混淆。
- x_tick_labels / y_tick_labels 为刻度数字区域。
- title 为标题文字区域。
- 不要输出数据点坐标，只输出区域框。

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
