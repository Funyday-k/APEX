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
    imageGeometry,
    heatmapOptions,
    setHeatmapOptions,
    setExtraction,
    setLoading,
    setError,
    semantics,
    regions,
  } = useStore();
  const { t } = useT();

  const run = async () => {
    if (!imageId) return;
    if (!imageGeometry) {
      setError(t('errImageNotReady'));
      return;
    }
    if (xScale === 'log' && xRefs.some((p) => p.data.x <= 0)) {
      setError(t('errLogCalibPositive'));
      return;
    }
    if (yScale === 'log' && yRefs.some((p) => p.data.y <= 0)) {
      setError(t('errLogCalibPositive'));
      return;
    }
    const cal = buildCalibration(xRefs, yRefs, xScale, yScale, imageGeometry);
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
      if (semantics) {
        payload.semantics = semantics;
        const colors = semantics.series_colors as Record<string, string> | undefined;
        if (colors) {
          payload.series_colors = Object.values(colors).filter(
            (c) => typeof c === 'string' && c.startsWith('#')
          );
        }
      }
      if (regions) {
        payload.regions = regions;
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
            onClick={() => {
              const natural = imageGeometry?.natural || { x: 300, y: 300 };
              setHeatmapOptions({
                colorbar_box: {
                  x0: Math.max(0, Math.round(natural.x - 50)),
                  y0: Math.round(natural.y * 0.15),
                  x1: Math.max(1, Math.round(natural.x - 20)),
                  y1: Math.round(natural.y * 0.85),
                },
                value_range: [0, 1],
                grid: [10, 10],
              });
            }}
          >
            {t('heatmapDefaults')}
          </button>
        </div>
      )}
      <button
        type="button"
        className="btn-primary"
        disabled={!imageGeometry}
        onClick={run}
      >
        {t('runExtract')}
      </button>
    </div>
  );
}
