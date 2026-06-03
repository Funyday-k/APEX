import { useT } from '../../i18n/useT';
import { autoAnalyze } from '../../services/api';
import { useStore } from '../../store/useStore';

export function AnalyzePanel() {
  const { imageId, imageUrl, chartMetadata, setAnalysis, setLoading, setError, setStep } =
    useStore();
  const { t } = useT();

  const run = async () => {
    if (!imageId) return;
    setLoading(true, t('analyzing'));
    setError(null);
    try {
      const res = await autoAnalyze(imageId);
      setAnalysis(
        res.chart_type,
        res.suggested_calibration,
        res.semantics,
        res.regions,
        res.chart_metadata
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const meta = chartMetadata;

  return (
    <div className="step-panel">
      <h2>{t('analyzeTitle')}</h2>
      {imageUrl && <img src={imageUrl} alt="preview" className="preview-thumb" />}
      <p className="hint">{t('analyzeHint')}</p>
      {meta && (
        <dl className="metadata-summary">
          {meta.title && (
            <>
              <dt>{t('metaTitle')}</dt>
              <dd>{meta.title}</dd>
            </>
          )}
          {(meta.x_quantity || meta.x_label) && (
            <>
              <dt>{t('metaXAxis')}</dt>
              <dd>
                {meta.x_quantity || meta.x_label}
                {meta.x_unit ? ` (${meta.x_unit})` : ''}
              </dd>
            </>
          )}
          {(meta.y_quantity || meta.y_label) && (
            <>
              <dt>{t('metaYAxis')}</dt>
              <dd>
                {meta.y_quantity || meta.y_label}
                {meta.y_unit ? ` (${meta.y_unit})` : ''}
              </dd>
            </>
          )}
          {meta.legend && meta.legend.length > 0 && (
            <>
              <dt>{t('metaLegend')}</dt>
              <dd>{meta.legend.join(' · ')}</dd>
            </>
          )}
        </dl>
      )}
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
