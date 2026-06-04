import { AnalysisInfoPanel } from './AnalysisInfoPanel';
import { ImageInfoCard } from './ImageInfoCard';
import { useT } from '../i18n/useT';
import { useStore } from '../store/useStore';

export function WizardFooter() {
  const { imageInfo, analysisDone, step } = useStore();
  const { t } = useT();

  if (step === 'upload' || !imageInfo?.fileName) return null;

  return (
    <footer className="wizard-footer">
      <ImageInfoCard info={imageInfo} />
      {analysisDone ? (
        <AnalysisInfoPanel />
      ) : (
        <section className="analysis-info-panel analysis-info-empty">
          <h3>{t('analysisInfoTitle')}</h3>
          <p className="hint">{t('analysisPending')}</p>
        </section>
      )}
    </footer>
  );
}
