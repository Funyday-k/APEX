# SciPlot-Extractor

从科研图表图像中精确提取结构化数据的本地 Web 应用（CV + VLM + 人机协同）。

**License:** [MIT](LICENSE)

## 状态

**规格完整实现** — 主框架 §1–17、附录 A/B/C、五步向导、扩展图类型、PDF 导出（[MIT](LICENSE)）。

- [实现进度](DOC/progress.md) · [任务清单](TASKS.md) · [文档索引](DOC/README.md)

## 快速开始（本地）

```bash
# 后端
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev
```

打开 **http://localhost:3000**，按五步向导完成上传 → 分析 → 标定 → 提取 → 导出。

## 一键 Docker 部署

```bash
cp .env.example .env    # 可选：设置 VLM_PROVIDER=openai 与 API Key
chmod +x scripts/compose-up.sh
./scripts/compose-up.sh
```

- 前端：http://localhost:3000  
- API 文档：http://localhost:8000/docs  

停止：`docker compose down`

## VLM 配置

| `VLM_PROVIDER` | 说明 |
|----------------|------|
| `stub`（默认） | 仅规则分类，无外部 API |
| `openai` | 需 `OPENAI_API_KEY` |
| `anthropic` | 需 `ANTHROPIC_API_KEY` |
| `local` | 本地 Qwen2-VL（见 [DOC/appendix/B-local-vlm.md](DOC/appendix/B-local-vlm.md)） |

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18, TypeScript, Vite, Konva, ECharts |
| 后端 | FastAPI, OpenCV, scikit-learn, Pydantic, SQLite |
| 部署 | Docker Compose, Nginx |

## 目录结构

```
Sciplot/
├── backend/       # FastAPI + CV 管线
├── frontend/      # React UI
├── data/          # 上传与结果（运行时）
├── DOC/           # 设计规格
├── scripts/       # compose-up.sh
└── LICENSE        # MIT
```
