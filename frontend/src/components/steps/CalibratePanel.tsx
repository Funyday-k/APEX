import { useT } from '../../i18n/useT';
import { autoAnalyze } from '../../services/api';
import { useStore } from '../../store/useStore';
import { AdvancedOptionsPanel } from '../AdvancedOptionsPanel';
import { ImageCanvas } from '../Canvas/ImageCanvas';
import { StepNav } from '../StepNav';

export function CalibratePanel() {
  const {
    chartType,
    setChartType,
    xRefs,
    yRefs,
    xScale,
    yScale,
    calibAxis,
    setCalibAxis,
    setScale,
    clearCalib,
    setStep,
    imageGeometry,
    suggestedTicks,
    applySuggestedCalibration,
    axisGeometry,
    axisConfidence,
    chartMetadata,
    showRegionOverlay,
    setShowRegionOverlay,
    autoCalibPending,
    analysisDone,
    imageId,
    setAnalysis,
    setLoading,
    setError,
    analyzeOptions,
  } = useStore();
  const { t } = useT();

  const hasSuggestedTicks =
    suggestedTicks &&
    ((suggestedTicks.x_ticks as unknown[])?.length ?? 0) >= 2 &&
    ((suggestedTicks.y_ticks as unknown[])?.length ?? 0) >= 2;

  const axisConfPct =
    axisConfidence &&
    Math.round((((axisConfidence.x_axis ?? 0) + (axisConfidence.y_axis ?? 0)) / 2) * 100);

  const reAnalyze = async () => {
    if (!imageId) return;
    setLoading(true, t('analyzing'));
    setError(null);
    try {
      const res = await autoAnalyze(imageId, {
        chart_type_override: analyzeOptions.chart_type_override || undefined,
        use_vlm_regions: analyzeOptions.use_vlm_regions,
        force_redetect_plot: analyzeOptions.force_redetect_plot,
      });
      setAnalysis(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-panel split">
      <div className="side-controls">
        <h2>{t('calibrateTitle')}</h2>
        <label>
          {t('chartType')}
          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value as typeof chartType)}
          >
            <option value="line">{t('chartLine')}</option>
            <option value="scatter">{t('chartScatter')}</option>
            <option value="bar">{t('chartBar')}</option>
            <option value="heatmap">{t('chartHeatmap')}</option>
            <option value="box">{t('chartBox')}</option>
          </select>
        </label>
        <label>
          {t('currentAxis')}
          <select value={calibAxis} onChange={(e) => setCalibAxis(e.target.value as 'x' | 'y')}>
            <option value="x">{t('axisX')}</option>
            <option value="y">{t('axisY')}</option>
          </select>
        </label>
        <label>
          {t('xScale')}
          <select value={xScale} onChange={(e) => setScale('x', e.target.value as 'linear' | 'log')}>
            <option value="linear">{t('scaleLinear')}</option>
            <option value="log">{t('scaleLog')}</option>
          </select>
        </label>
        <label>
          {t('yScale')}
          <select value={yScale} onChange={(e) => setScale('y', e.target.value as 'linear' | 'log')}>
            <option value="linear">{t('scaleLinear')}</option>
            <option value="log">{t('scaleLog')}</option>
          </select>
        </label>
        <p className="hint">{t('calibrateHint', { x: xRefs.length, y: yRefs.length })}</p>
        <p className="hint">{t('calibModalShort')}</p>
        {axisGeometry && axisConfPct != null && (
          <p className="hint metadata-inline">
            {t('axisConfidence', { pct: axisConfPct })}
          </p>
        )}
        {autoCalibPending && (
          <p className="warning">{t('autoCalibPendingShort')}</p>
        )}
        {chartMetadata && (chartMetadata.x_quantity || chartMetadata.y_quantity) && (
          <p className="hint metadata-inline">
            {chartMetadata.x_quantity || chartMetadata.x_label}
            {chartMetadata.x_unit ? ` [${chartMetadata.x_unit}]` : ''} ·{' '}
            {chartMetadata.y_quantity || chartMetadata.y_label}
            {chartMetadata.y_unit ? ` [${chartMetadata.y_unit}]` : ''}
          </p>
        )}
        <label className="checkbox-inline">
          <input
            type="checkbox"
            checked={showRegionOverlay}
            onChange={(e) => setShowRegionOverlay(e.target.checked)}
          />
          {t('showRegionOverlay')}
        </label>
        {hasSuggestedTicks && (
          <button type="button" className="btn-muted" onClick={applySuggestedCalibration}>
            {t('applyAiAxisCalibration')}
          </button>
        )}
        {analysisDone && (
          <button type="button" className="btn-muted" onClick={reAnalyze}>
            {t('reAnalyze')}
          </button>
        )}
        <AdvancedOptionsPanel mode="analyze" />
        <div className="btn-row">
          <StepNav backTo="analyze" />
          <button type="button" className="btn-muted" onClick={clearCalib}>
            {t('clearCalib')}
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={xRefs.length < 2 || yRefs.length < 2 || !imageGeometry}
            onClick={() => setStep('extract')}
          >
            {t('nextExtract')}
          </button>
        </div>
      </div>
      <div className="canvas-wrap">
        <ImageCanvas mode="calibrating" />
      </div>
    </div>
  );
}
