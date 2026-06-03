# SciPlot-Extractor 文档索引

**项目代号**：SciPlot-Extractor  
**目标**：跨平台、易部署的本地 Web 应用，结合传统 CV 与大模型视觉（VLM），从科研图表中精确提取结构化数据。

**核心原则**：数值由 CV 精确提取，VLM 仅负责语义理解与辅助标定，人机协同保证最终准确性。

**许可**：[MIT](../LICENSE)

---

## 文档结构

| 文档 | 内容 |
|------|------|
| [core/01-framework.md](core/01-framework.md) | §1–17：架构、技术栈、部署、后端十模块、API、测试 |
| [appendix/A-error-bars-fit.md](appendix/A-error-bars-fit.md) | 附录 A：误差棒与拟合曲线检测 |
| [appendix/B-local-vlm.md](appendix/B-local-vlm.md) | 附录 B：本地 Qwen2-VL 部署与量化 |
| [appendix/C-frontend-wizard.md](appendix/C-frontend-wizard.md) | 附录 C：前端五步向导与校正画布 |
| [core/02-integration.md](core/02-integration.md) | 三模块整合要点与 orchestrator 增补 |
| [roadmap.md](roadmap.md) | 开发路线图与设计原则 |
| [progress.md](progress.md) | **实现进度与 API 说明** |
| [Proposal.md](Proposal.md) | 完整合订本（归档，优先阅读分册） |

---

## 实现状态

**代码已与本文档规格对齐**（见 [progress.md](progress.md)）。分册为设计参考；以仓库 `backend/`、`frontend/` 为准。

## 处理管线（一览）

```
原图 → 预处理 → 类型识别 → 坐标标定 → CV提取
                              ↓
                    VLM语义 ──→ 交叉验证 → 人工校正 → 导出
```

---

## 推荐目录结构（实现时）

见 [core/01-framework.md §2.2](core/01-framework.md)：`sciplot-extractor/` 下的 `backend/`、`frontend/`、`models/` 布局。
