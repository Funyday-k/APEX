import { useEffect } from 'react';
import { LanguageSwitcher } from './components/LanguageSwitcher';
import { LoadingOverlay } from './components/LoadingOverlay';
import { StepIndicator } from './components/StepIndicator';
import { ReviewPanel } from './components/review/ReviewPanel';
import { AnalyzePanel } from './components/steps/AnalyzePanel';
import { CalibratePanel } from './components/steps/CalibratePanel';
import { ExtractPanel } from './components/steps/ExtractPanel';
import { UploadPanel } from './components/steps/UploadPanel';
import { useT } from './i18n/useT';
import { useStore } from './store/useStore';

export default function App() {
  const { step, error, locale } = useStore();
  const { t } = useT();

  useEffect(() => {
    document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en';
  }, [locale]);

  return (
    <div className="app wizard">
      <header className="header wizard-header">
        <div>
          <h1>{t('appTitle')}</h1>
          <p>{t('appSubtitle')}</p>
        </div>
        <div className="header-actions">
          <LanguageSwitcher />
          <StepIndicator current={step} />
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}
      <LoadingOverlay />

      <main className="wizard-main">
        {step === 'upload' && <UploadPanel />}
        {step === 'analyze' && <AnalyzePanel />}
        {step === 'calibrate' && <CalibratePanel />}
        {step === 'extract' && <ExtractPanel />}
        {step === 'review' && <ReviewPanel />}
      </main>
    </div>
  );
}
