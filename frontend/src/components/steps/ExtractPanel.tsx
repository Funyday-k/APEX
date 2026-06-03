import { extractData } from '../../services/api';
import { buildCalibration, useStore } from '../../store/useStore';

export function ExtractPanel() {
  const {
    imageId,
    chartType,
    xRefs,
    yRefs,
    xScale,
    yScale,
    heatmapOptions,
    setHeatmapOptions,
    setExtraction,
    setLoading,
    setError,
  } = useStore();

  const run = async () => {
    if (!imageId) return;
    const cal = buildCalibration(xRefs, yRefs, xScale, yScale);
    if (!cal) {
      setError('请完成 X/Y 各 2 个标定点');
      return;
    }
    if (chartType === 'heatmap' && !heatmapOptions) {
      setError('热图需填写 colorbar 区域与数值范围');
      return;
    }
    setLoading(true, 'CV 提取中…');
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        image_id: imageId,
        chart_type: chartType,
        calibration: cal,
      };
      if (chartType === 'heatmap' && heatmapOptions) {
        payload.heatmap_options = heatmapOptions;
      }
      const res = await extractData(payload);
      setExtraction(res, cal);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-panel">
      <h2>执行提取</h2>
      <p className="hint">类型: {chartType} · 标定已完成</p>
      {chartType === 'heatmap' && (
        <div className="heatmap-form">
          <p>热图参数（像素坐标与数值范围，可按图估算）:</p>
          <button
            type="button"
            className="btn-muted"
            onClick={() =>
              setHeatmapOptions({
                colorbar_box: { x0: 10, y0: 10, x1: 40, y1: 200 },
                value_range: [0, 1],
                grid: [10, 10],
              })
            }
          >
            使用默认热图参数
          </button>
        </div>
      )}
      <button type="button" className="btn-primary" onClick={run}>
        运行 CV + VLM 提取
      </button>
    </div>
  );
}
