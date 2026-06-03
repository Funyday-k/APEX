import { useT } from '../../i18n/useT';
import { exportResult } from '../../services/api';
import { useStore } from '../../store/useStore';
import { RebuiltChart } from '../Preview/RebuiltChart';
import { ReviewCanvas } from './ReviewCanvas';

export function ReviewPanel() {
  const {
    imageId,
    series,
    chartType,
    flags,
    overallConfidence,
    fitCurves,
    pixelDisplayMode,
    showFitCurves,
    setPixelDisplayMode,
    setShowFitCurves,
    setLoading,
    setError,
    reset,
    suggestedRemovals,
    applySuggestedRemovals,
    chartMetadata,
    showRegionOverlay,
    setShowRegionOverlay,
  } = useStore();
  const { t } = useT();

  const totalPoints = series.reduce((n, s) => n + s.points.length, 0);

  const handleExport = async (format: 'csv' | 'json' | 'excel' | 'pdf') => {
    if (!imageId || !series.length) {
      setError(t('errNoSeries'));
      return;
    }
    setLoading(true, t('exporting'));
    try {
      const blob = await exportResult(imageId, format, {
        chart_type: chartType,
        series,
        title: chartMetadata?.title,
        x_label: chartMetadata?.x_label,
        y_label: chartMetadata?.y_label,
        x_quantity: chartMetadata?.x_quantity,
        y_quantity: chartMetadata?.y_quantity,
        x_unit: chartMetadata?.x_unit,
        y_unit: chartMetadata?.y_unit,
        legend: chartMetadata?.legend,
        overall_confidence: overallConfidence,
        low_confidence_flags: flags,
        metadata: { fit_curves: fitCurves },
      });
      const ext =
        format === 'json' ? 'json' : format === 'excel' ? 'xlsx' : format === 'pdf' ? 'pdf' : 'csv';
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `apex.${ext}`;
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
        <p className="hint">
          {t('reviewStats', { series: series.length, points: totalPoints })}
        </p>
        {chartMetadata?.title && (
          <p className="hint">
            {t('metaTitle')}: {chartMetadata.title}
          </p>
        )}
        {suggestedRemovals.length > 0 && (
          <div className="removal-suggestions">
            <p className="warning">
              {t('suggestedRemovalsCount', { n: suggestedRemovals.length })}
            </p>
            <ul className="flags-list compact">
              {suggestedRemovals.slice(0, 8).map((r, i) => (
                <li key={i}>
                  #{r.series_idx + 1}-{r.point_idx + 1}: {r.reason} (
                  {(r.confidence * 100).toFixed(0)}%)
                </li>
              ))}
              {suggestedRemovals.length > 8 && (
                <li>…{suggestedRemovals.length - 8} more</li>
              )}
            </ul>
            <button type="button" className="btn-primary" onClick={applySuggestedRemovals}>
              {t('applySuggestedRemovals')}
            </button>
          </div>
        )}
        {flags.length > 0 && (
          <ul className="flags-list">
            {flags.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        )}
        <div className="review-controls">
          <label>
            <input
              type="checkbox"
              checked={showRegionOverlay}
              onChange={(e) => setShowRegionOverlay(e.target.checked)}
            />
            {t('showRegionOverlay')}
          </label>
          <label>
            <input
              type="radio"
              checked={pixelDisplayMode === 'data'}
              onChange={() => setPixelDisplayMode('data')}
            />
            {t('pixelModeData')}
          </label>
          <label>
            <input
              type="radio"
              checked={pixelDisplayMode === 'detected'}
              onChange={() => setPixelDisplayMode('detected')}
            />
            {t('pixelModeDetected')}
          </label>
          {fitCurves.length > 0 && (
            <label>
              <input
                type="checkbox"
                checked={showFitCurves}
                onChange={(e) => setShowFitCurves(e.target.checked)}
              />
              {t('showFitCurves')}
            </label>
          )}
        </div>
        <p className="hint">{t('reviewDeleteHint')}</p>
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
