import type { Step } from '../store/useStore';
import { useStore } from '../store/useStore';
import { useT } from '../i18n/useT';

const STEP_ORDER: Step[] = ['upload', 'analyze', 'calibrate', 'extract', 'review'];

type Props = {
  backTo?: Step;
  showBack?: boolean;
  showForward?: boolean;
  forwardLabel?: string;
  forwardDisabled?: boolean;
  onForward?: () => void;
};

export function StepNav({
  backTo,
  showBack = true,
  showForward = false,
  forwardLabel,
  forwardDisabled,
  onForward,
}: Props) {
  const { step, setStep } = useStore();
  const { t } = useT();

  const goBack = () => {
    if (backTo) setStep(backTo);
  };

  return (
    <div className="step-nav">
      {showBack && backTo && (
        <button type="button" className="btn-muted" onClick={goBack}>
          {t('backToStep', { step: t(stepLabelKey(backTo)) })}
        </button>
      )}
      {showForward && onForward && (
        <button
          type="button"
          className="btn-primary"
          disabled={forwardDisabled}
          onClick={onForward}
        >
          {forwardLabel || t('nextStep')}
        </button>
      )}
    </div>
  );
}

function stepLabelKey(s: Step): 'stepUpload' | 'stepAnalyze' | 'stepCalibrate' | 'stepExtract' | 'stepReview' {
  const map = {
    upload: 'stepUpload',
    analyze: 'stepAnalyze',
    calibrate: 'stepCalibrate',
    extract: 'stepExtract',
    review: 'stepReview',
  } as const;
  return map[s];
}

export function stepIndex(s: Step): number {
  return STEP_ORDER.indexOf(s);
}

export function canNavigateTo(target: Step, current: Step): boolean {
  return stepIndex(target) <= stepIndex(current);
}
