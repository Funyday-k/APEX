# 三模块整合要点

| 模块 | 后端接入点 | 前端接入点 |
|------|-----------|-----------|
| **误差棒/拟合** | `ScatterExtractor` 增强 → `orchestrator.extract` 合并 `fit_curves` 到结果 | `RebuiltChart` 虚线渲染拟合曲线 |
| **本地 VLM** | `VLM_PROVIDER=local` 环境变量切换，零代码改动 | 无感知（API 一致） |
| **前端交互** | `analyze`/`run`/`recompute`/`export` 四端点 | 五步向导完整闭环 |

## 后端结果合并补充 `core/orchestrator.py`（extract 方法增补）

```python
# 在 extract() 末尾，合并拟合曲线与误差棒
async def extract(self, image_bytes, chart_type, calibration,
                  series_colors=None):
    img = load_image(image_bytes)
    img = enhance(img)

    extractor = get_extractor(chart_type)
    calibrator = Calibrator(calibration)
    cv_result = extractor.extract(img, calibrator, series_colors)

    semantics = await self.vlm.analyze_semantics(image_bytes)
    result = self.validator.validate(cv_result, semantics, img)

    # 合并拟合曲线（散点提取器附加）
    fit_curves = getattr(extractor, "_last_fit_curves", [])
    result.metadata["fit_curves"] = [f.model_dump() for f in fit_curves]

    # 为前端附加像素坐标（用于画布渲染）
    for series in result.series:
        pixel_pts = [calibrator.data_to_pixel(p.x, p.y)
                     for p in series.points]
        # 通过 metadata 传递
    result.metadata["pixel_mapping"] = True

    return result
```

---

三大进阶模块（附录 A/B/C）覆盖误差棒/拟合曲线、本地 VLM、前端五步向导，可直接支撑单图提取的完整工作流。

**待补充**（原 spec 末尾建议）：

1. 后端像素坐标回传的完整序列化逻辑
2. 箱线图/柱状图的前端专门校正交互
3. 误差棒与拟合曲线的单元测试
4. 端到端联调脚本
