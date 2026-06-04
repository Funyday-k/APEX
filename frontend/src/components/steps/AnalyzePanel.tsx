import { useT } from '../../i18n/useT';
import { autoAnalyze } from '../../services/api';
import { AdvancedOptionsPanel } from '../AdvancedOptionsPanel';
import { ImageCanvas } from '../Canvas/ImageCanvas';
import { StepNav } from '../StepNav';
import { useStore } from '../../store/useStore';

export function AnalyzePanel() {
  const {
    imageId,
    imageUrl,
    analysisDone,
    setAnalysis,
    setLoading,
    setError,
    setStep,
    analyzeOptions,
    autoCalibConfidence,
    autoCalibPending,
    applySuggestedCalibration,
  } = useStore();
  const { t } = useT();

  const run = async () => {
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

  if (!imageUrl) return null;

  return (
    <div className="step-panel split analyze-panel">
      <div className="side-controls">
        <h2>{t('analyzeTitle')}</h2>
        <p className="hint">{t('analyzeHint')}</p>
        <AdvancedOptionsPanel mode="analyze" />
        <div className="btn-row">
          <button type="button" className="btn-primary" onClick={run}>
            {analysisDone ? t('reAnalyze') : t('startAnalyze')}
          </button>
          <StepNav backTo="upload" />
          {analysisDone && (
            <button type="button" className="btn-primary" onClick={() => setStep('calibrate')}>
              {t('nextCalibrate')}
            </button>
          )}
          {!analysisDone && (
            <button type="button" className="btn-muted" onClick={() => setStep('calibrate')}>
              {t('skipToCalibrate')}
            </button>
          )}
        </div>
        {analysisDone && (
          <div className="analyze-results">
            {autoCalibConfidence > 0 && (
              <p className="hint">
                {autoCalibPending
                  ? t('autoCalibPending', { pct: Math.round(autoCalibConfidence * 100) })
                  : t('autoCalibApplied', { pct: Math.round(autoCalibConfidence * 100) })}
              </p>
            )}
            {autoCalibPending && (
              <button type="button" className="btn-muted" onClick={applySuggestedCalibration}>
                {t('applyAiAxisCalibration')}
              </button>
            )}
          </div>
        )}
      </div>
      <div className="canvas-wrap">
        <ImageCanvas mode="preview" />
      </div>
    </div>
  );
}
