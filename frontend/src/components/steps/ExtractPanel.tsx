import { useT } from '../../i18n/useT';
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
  const { t } = useT();

  const run = async () => {
    if (!imageId) return;
    const cal = buildCalibration(xRefs, yRefs, xScale, yScale);
    if (!cal) {
      setError(t('errCalibIncomplete'));
      return;
    }
    if (chartType === 'heatmap' && !heatmapOptions) {
      setError(t('errHeatmapOptions'));
      return;
    }
    setLoading(true, t('extracting'));
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
      <h2>{t('extractTitle')}</h2>
      <p className="hint">{t('extractHint', { type: chartType })}</p>
      {chartType === 'heatmap' && (
        <div className="heatmap-form">
          <p>{t('heatmapParams')}</p>
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
            {t('heatmapDefaults')}
          </button>
        </div>
      )}
      <button type="button" className="btn-primary" onClick={run}>
        {t('runExtract')}
      </button>
    </div>
  );
}
