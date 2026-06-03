import { exportResult } from '../../services/api';
import { useStore } from '../../store/useStore';
import { RebuiltChart } from '../Preview/RebuiltChart';
import { ReviewCanvas } from './ReviewCanvas';

export function ReviewPanel() {
  const {
    imageId,
    series,
    flags,
    overallConfidence,
    fitCurves,
    setLoading,
    setError,
    reset,
  } = useStore();

  const handleExport = async (format: 'csv' | 'json' | 'excel' | 'pdf') => {
    if (!imageId || !series.length) return;
    setLoading(true, '导出中…');
    try {
      const blob = await exportResult(imageId, format, series);
      const ext =
        format === 'json' ? 'json' : format === 'excel' ? 'xlsx' : format === 'pdf' ? 'pdf' : 'csv';
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `sciplot.${ext}`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-panel review">
      <div className="review-side">
        <h2>校正与导出</h2>
        <p>整体置信度: {(overallConfidence * 100).toFixed(0)}%</p>
        {flags.length > 0 && (
          <ul className="flags-list">
            {flags.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        )}
        {fitCurves.length > 0 && (
          <p className="hint">已识别 {fitCurves.length} 条拟合曲线（见重建图虚线）</p>
        )}
        <div className="btn-row wrap">
          <button type="button" onClick={() => handleExport('csv')}>
            CSV
          </button>
          <button type="button" onClick={() => handleExport('json')}>
            JSON
          </button>
          <button type="button" onClick={() => handleExport('excel')}>
            Excel
          </button>
          <button type="button" onClick={() => handleExport('pdf')}>
            PDF 报告
          </button>
          <button type="button" className="btn-muted" onClick={reset}>
            新图
          </button>
        </div>
        <RebuiltChart />
      </div>
      <div className="canvas-wrap">
        <ReviewCanvas />
      </div>
    </div>
  );
}
