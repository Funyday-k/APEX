import type { Step } from '../store/useStore';

const STEPS: { id: Step; label: string }[] = [
  { id: 'upload', label: '上传' },
  { id: 'analyze', label: '分析' },
  { id: 'calibrate', label: '标定' },
  { id: 'extract', label: '提取' },
  { id: 'review', label: '校正导出' },
];

const ORDER = STEPS.map((s) => s.id);

export function StepIndicator({ current }: { current: Step }) {
  const idx = ORDER.indexOf(current);
  return (
    <nav className="step-indicator">
      {STEPS.map((s, i) => (
        <span
          key={s.id}
          className={`step-item ${i === idx ? 'active' : ''} ${i < idx ? 'done' : ''}`}
        >
          {i + 1}. {s.label}
        </span>
      ))}
    </nav>
  );
}
