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
  "x_label": "X轴标签（含单位），无则 null",
  "y_label": "Y轴标签（含单位），无则 null",
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

直接输出 JSON："""
