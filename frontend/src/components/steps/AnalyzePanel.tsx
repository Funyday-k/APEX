import { useT } from '../../i18n/useT';
import { autoAnalyze } from '../../services/api';
import { useStore } from '../../store/useStore';

export function AnalyzePanel() {
  const { imageId, imageUrl, setAnalysis, setLoading, setError, setStep } = useStore();
  const { t } = useT();

  const run = async () => {
    if (!imageId) return;
    setLoading(true, t('analyzing'));
    setError(null);
    try {
      const res = await autoAnalyze(imageId);
      setAnalysis(res.chart_type, res.suggested_calibration, res.semantics);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-panel">
      <h2>{t('analyzeTitle')}</h2>
      {imageUrl && <img src={imageUrl} alt="preview" className="preview-thumb" />}
      <p className="hint">{t('analyzeHint')}</p>
      <div className="btn-row">
        <button type="button" className="btn-primary" onClick={run}>
          {t('startAnalyze')}
        </button>
        <button type="button" className="btn-muted" onClick={() => setStep('calibrate')}>
          {t('skipToCalibrate')}
        </button>
      </div>
    </div>
  );
}
