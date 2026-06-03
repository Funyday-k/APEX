import type { Step } from '../store/useStore';
import { useT } from '../i18n/useT';

const STEPS: { id: Step; key: 'stepUpload' | 'stepAnalyze' | 'stepCalibrate' | 'stepExtract' | 'stepReview' }[] = [
  { id: 'upload', key: 'stepUpload' },
  { id: 'analyze', key: 'stepAnalyze' },
  { id: 'calibrate', key: 'stepCalibrate' },
  { id: 'extract', key: 'stepExtract' },
  { id: 'review', key: 'stepReview' },
];

export function StepIndicator({ current }: { current: Step }) {
  const { t } = useT();
  const idx = STEPS.findIndex((s) => s.id === current);

  return (
    <nav className="step-indicator">
      {STEPS.map((s, i) => (
        <span
          key={s.id}
          className={`step-item ${i === idx ? 'active' : ''} ${i < idx ? 'done' : ''}`}
        >
          {i + 1}. {t(s.key)}
        </span>
      ))}
    </nav>
  );
}
