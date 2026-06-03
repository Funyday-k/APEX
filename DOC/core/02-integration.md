# 三模块整合要点

| 模块 | 后端接入点 | 前端接入点 |
|------|-----------|-----------|
| **误差棒/拟合** | `ScatterExtractor` + `ErrorBarDetector` / `FitCurveAnalyzer` → `metadata.fit_curves` | `RebuiltChart` 虚线渲染拟合曲线 |
| **本地 VLM** | `VLM_PROVIDER=local` + `scripts/download_model.py` | 无感知 |
| **前端交互** | 五步向导 API | `UploadPanel` → `ReviewPanel` |

## 后端 `extract()` 合并（已实现）

`core/orchestrator.py` 在提取后写入 `metadata.fit_curves` 与 `pixel_mapping`；API 通过 `enrich_series_for_api` 返回 `pixel_points` 与 `errors`。

## 像素坐标回传

`enrich_series_for_api` 为每个系列附加 `pixel_points`，供 Konva 画布渲染与拖拽校正。
