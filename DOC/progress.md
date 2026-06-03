# 实现进度

**状态：DOC 主规格 + 附录 A/B/C 均已落地（代码实现）。**

| 模块 | 状态 |
|------|------|
| §1–17 主框架 | ✅ |
| 附录 A 误差棒/拟合 | ✅ |
| 附录 B 本地 VLM 脚本与配置 | ✅（权重需自行下载） |
| 附录 C 五步向导 | ✅ |
| MIT License | ✅ |

## 后端模块清单

| 路径 | 功能 |
|------|------|
| `preprocessing/` | 加载、增强、绘图区 |
| `classification/` | 规则 + VLM 分类 |
| `calibration/` | 标定、刻度、对数轴 |
| `extractors/` | line, scatter, bar, heatmap, box, error_bar, fit_curve |
| `ocr/` | PaddleOCR（可选）+ postprocess |
| `vlm/` | stub, openai, anthropic, local_qwen, local_config |
| `validation/` | confidence, cross_validator |
| `export/` | CSV/Excel/JSON/PDF |
| `api/` | 全套 REST |
| `tests/` | calibration, parser, extraction, benchmark runner |

## 前端

五步流程：`upload` → `analyze` → `calibrate` → `extract` → `review`

支持图表类型：line, scatter, bar, heatmap, box；X/Y 线性/对数标定；拖拽校正；拟合曲线虚线预览；PDF 导出。

## VLM / OCR

| 变量 | 说明 |
|------|------|
| `VLM_PROVIDER` | stub / openai / anthropic / local |
| `OCR_ENABLED=0` | 禁用 OCR |
| 无 paddle | OCR 自动降级为空列表 |

## 热图

提取时需 `heatmap_options`（colorbar 框、数值范围、网格）。前端「使用默认热图参数」可快速试用。

## 测试

```bash
cd backend && pytest tests/ -q
```

6 tests passed（含合成折线图提取 smoke test）。
