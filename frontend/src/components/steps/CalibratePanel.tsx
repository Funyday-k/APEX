import { useT } from '../../i18n/useT';
import { useStore } from '../../store/useStore';
import { ImageCanvas } from '../Canvas/ImageCanvas';

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
    chartMetadata,
    showRegionOverlay,
    setShowRegionOverlay,
  } = useStore();
  const { t } = useT();

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
        {suggestedTicks && imageGeometry && (
          <button type="button" className="btn-muted" onClick={applySuggestedCalibration}>
            {t('applySuggestedTicks')}
          </button>
        )}
        <div className="btn-row">
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
