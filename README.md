# SciPlot-Extractor

从科研图表图像中精确提取结构化数据的本地 Web 应用（CV + VLM + 人机协同）。

## 状态

**设计阶段** — 完整技术规格见 [`DOC/`](DOC/)，实现尚未开始。

## 文档

- [文档索引](DOC/README.md)
- [主框架规格](DOC/core/01-framework.md)
- [开发路线图](DOC/roadmap.md)
- [实现任务规划](TASKS.md)

## 核心原则

- 数值由 **OpenCV / 传统 CV** 从像素提取
- **VLM** 仅负责图类型、图例、轴标签等语义
- 用户可在画布上 **拖拽校正**，并对比重建图

## 技术栈（计划）

| 层 | 技术 |
|----|------|
| 前端 | React 18, TypeScript, Vite, Konva, ECharts, Zustand |
| 后端 | FastAPI, OpenCV, PaddleOCR |
| VLM | OpenAI / Anthropic API，可选本地 Qwen2-VL |
| 部署 | Docker Compose, SQLite |

## 许可证

待定。
