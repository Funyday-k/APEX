# 实现任务规划

> 与 [DOC/](DOC/) 规格对齐；**全部主规格已实现**。

## Phase 0–2 ✅ MVP

仓库、后端 CV 管线、前端交互。

## Phase 3 ✅ Docker

- [x] docker-compose + healthcheck
- [x] `scripts/compose-up.sh`
- [x] PaddleOCR 可选依赖 `requirements-ocr.txt`

## Phase 4 ✅ VLM

- [x] OpenAI / Anthropic / stub / local 入口
- [x] 交叉验证与置信度
- [x] PaddleOCR（可选安装，未安装时降级为空）

## Phase 5 ✅ 扩展图类型

- [x] `bar_chart`, `heatmap`, `box_plot` 提取器
- [x] 误差棒 `error_bar.py`、拟合曲线 `fit_curve.py`（散点图集成）
- [x] 对数轴标定（前后端 linear/log）

## Phase 6 ✅ 体验与工具

- [x] 五步向导 UI（附录 C）
- [x] PDF 报告 `export/report.py`
- [x] 基准测试脚本 `tests/benchmark/run_benchmark.py`
- [x] `scripts/download_model.py`、`vlm/local_config.py`
- [x] MIT 许可

## 可选 / 运维

- [ ] 本地 Qwen 需自行下载权重并安装 torch/transformers
- [ ] Docker 环境需本机安装 Docker 后运行 `compose-up.sh`
- [ ] 基准测试集需用户自备 truth/pred CSV 对

---

## 开发

```bash
cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

## Docker

```bash
./scripts/compose-up.sh
```
