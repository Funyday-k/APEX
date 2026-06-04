import type { Step } from '../store/useStore';
import { useStore } from '../store/useStore';
import { useT } from '../i18n/useT';
import { canNavigateTo } from './StepNav';

const STEPS: { id: Step; key: 'stepUpload' | 'stepAnalyze' | 'stepCalibrate' | 'stepExtract' | 'stepReview' }[] = [
  { id: 'upload', key: 'stepUpload' },
  { id: 'analyze', key: 'stepAnalyze' },
  { id: 'calibrate', key: 'stepCalibrate' },
  { id: 'extract', key: 'stepExtract' },
  { id: 'review', key: 'stepReview' },
];

export function StepIndicator({ current }: { current: Step }) {
  const { t } = useT();
  const { goToStep, maxStepReached } = useStore();
  const idx = STEPS.findIndex((s) => s.id === current);

  return (
    <nav className="step-indicator">
      {STEPS.map((s, i) => {
        const clickable = canNavigateTo(s.id, maxStepReached) && s.id !== current;
        return (
          <button
            key={s.id}
            type="button"
            className={`step-item ${i === idx ? 'active' : ''} ${i < idx ? 'done' : ''} ${
              clickable ? 'clickable' : ''
            }`}
            disabled={!clickable}
            onClick={() => clickable && goToStep(s.id)}
          >
            {i + 1}. {t(s.key)}
          </button>
        );
      })}
    </nav>
  );
}
