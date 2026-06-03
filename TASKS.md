# 实现任务规划

基于 [DOC/](DOC/) 规格拆解的执行顺序。每项对应路线图阶段，可勾选跟踪进度。

---

## Phase 0：仓库与骨架（当前）

- [x] 初始化 Git 仓库
- [x] 整理 Proposal 为分册文档
- [ ] 创建 `backend/`、`frontend/` 目录骨架（空包 + `requirements.txt` / `package.json` 占位）
- [ ] 添加 `.env.example`、`docker-compose.yml` 骨架
- [ ] 配置 CI（lint / 类型检查，可选）

---

## Phase 1：MVP 后端

参考：[DOC/core/01-framework.md](DOC/core/01-framework.md) §4–8, §15–16

1. **核心模型** — `core/schemas.py`（`CalibrationConfig`, `ExtractionResult`, …）
2. **预处理** — `loader`, `enhance`, `plot_area`
3. **标定** — `transforms`, `calibrator`, `axis_detector`, `tick_detector`
4. **提取器** — `base`, `color_segmentation`, `line_chart`, `scatter`
5. **调度器** — `orchestrator.py` 串联预处理 → 标定 → 提取
6. **API** — `upload`, `extract/run`, `calibrate/recompute`, `export`（CSV）
7. **存储** — SQLite + 上传文件目录

**验收**：对一张折线图/散点图，手动 4 点标定后能导出 CSV，MAPE 可人工目测合理。

---

## Phase 2：MVP 前端

参考：§13 + [DOC/appendix/C-frontend-wizard.md](DOC/appendix/C-frontend-wizard.md)（可先简化版）

1. Vite + React + TS 脚手架
2. `upload` → `analyze`（可先 mock）→ 标定画布（Konva）
3. 提取结果叠加 + 拖拽触发 `recompute`
4. ECharts 重建预览
5. CSV 导出按钮

**验收**：浏览器内完成上传 → 标定 → 提取 → 导出闭环。

---

## Phase 3：Docker 与部署

参考：§3

- `backend/Dockerfile`, `frontend/Dockerfile`
- `docker-compose.yml`（backend + frontend + 可选 redis）
- `README` 一键启动说明

---

## Phase 4：VLM 集成

参考：§6, §10, §11

- `vlm/provider` 抽象 + OpenAI provider
- 自动图类型建议、语义字段、置信度
- `cross_validator` 融合 CV 与 VLM

---

## Phase 5：扩展图类型与附录 A

- `bar_chart`, `heatmap`, `box_plot`
- [附录 A](DOC/appendix/A-error-bars-fit.md)：`error_bar.py`, `fit_curve.py`，增强 `scatter`

---

## Phase 6：体验与本地 VLM

- [附录 C](DOC/appendix/C-frontend-wizard.md) 五步向导完整 UI
- [附录 B](DOC/appendix/B-local-vlm.md) 本地 Qwen2-VL
- PDF 报告、基准测试集 `tests/benchmark/`

---

## 建议的下一步（Agent / 开发者）

1. 执行 Phase 0 剩余项：生成 `sciplot-extractor` 目录树（与 spec §2.2 一致）
2. 从 `core/schemas.py` + `calibration/transforms.py` 开始编码（可单测驱动）
3. 用一张样例图打通 `orchestrator` 最小路径后再接 FastAPI
