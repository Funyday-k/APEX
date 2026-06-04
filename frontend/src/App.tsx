import { useEffect } from 'react';
import { LanguageSwitcher } from './components/LanguageSwitcher';
import { LoadingOverlay } from './components/LoadingOverlay';
import { StepIndicator } from './components/StepIndicator';
import { ReviewPanel } from './components/review/ReviewPanel';
import { AnalyzePanel } from './components/steps/AnalyzePanel';
import { CalibratePanel } from './components/steps/CalibratePanel';
import { ExtractPanel } from './components/steps/ExtractPanel';
import { UploadPanel } from './components/steps/UploadPanel';
import { WizardFooter } from './components/WizardFooter';
import { useStore } from './store/useStore';

export default function App() {
  const { step, error, locale } = useStore();
  useEffect(() => {
    document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en';
  }, [locale]);

  return (
    <div className="app wizard">
      <header className="header wizard-header">
        <div className="brand">
          <h1 className="brand-apex">APEX</h1>
          <p className="brand-tagline">Automatic Plot Extractor for science</p>
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
        <WizardFooter />
      </main>
    </div>
  );
}
