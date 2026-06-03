import { useT } from '../../i18n/useT';
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
  const { t } = useT();

  const handleExport = async (format: 'csv' | 'json' | 'excel' | 'pdf') => {
    if (!imageId || !series.length) return;
    setLoading(true, t('exporting'));
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
        <h2>{t('reviewTitle')}</h2>
        <p>{t('confidence', { pct: (overallConfidence * 100).toFixed(0) })}</p>
        {flags.length > 0 && (
          <ul className="flags-list">
            {flags.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        )}
        {fitCurves.length > 0 && (
          <p className="hint">{t('fitCurvesHint', { n: fitCurves.length })}</p>
        )}
        <div className="btn-row wrap">
          <button type="button" onClick={() => handleExport('csv')}>
            {t('exportCsv')}
          </button>
          <button type="button" onClick={() => handleExport('json')}>
            {t('exportJson')}
          </button>
          <button type="button" onClick={() => handleExport('excel')}>
            {t('exportExcel')}
          </button>
          <button type="button" onClick={() => handleExport('pdf')}>
            {t('exportPdf')}
          </button>
          <button type="button" className="btn-muted" onClick={reset}>
            {t('newImage')}
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
