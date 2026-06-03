import { LoadingOverlay } from './components/LoadingOverlay';
import { StepIndicator } from './components/StepIndicator';
import { ReviewPanel } from './components/review/ReviewPanel';
import { AnalyzePanel } from './components/steps/AnalyzePanel';
import { CalibratePanel } from './components/steps/CalibratePanel';
import { ExtractPanel } from './components/steps/ExtractPanel';
import { UploadPanel } from './components/steps/UploadPanel';
import { useStore } from './store/useStore';

export default function App() {
  const { step, error } = useStore();

  return (
    <div className="app wizard">
      <header className="header wizard-header">
        <div>
          <h1>SciPlot Extractor</h1>
          <p>科研图表数据提取</p>
        </div>
        <StepIndicator current={step} />
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
