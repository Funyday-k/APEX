import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

const base = {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

export function IconZoomIn(props: IconProps) {
  return (
    <svg {...base} {...props} aria-hidden>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.35-4.35M11 8v6M8 11h6" />
    </svg>
  );
}

export function IconZoomOut(props: IconProps) {
  return (
    <svg {...base} {...props} aria-hidden>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.35-4.35M8 11h6" />
    </svg>
  );
}

export function IconFitWindow(props: IconProps) {
  return (
    <svg {...base} {...props} aria-hidden>
      <path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" />
    </svg>
  );
}

export function IconResetView(props: IconProps) {
  return (
    <svg {...base} {...props} aria-hidden>
      <path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5" />
    </svg>
  );
}

export function IconPan(props: IconProps) {
  return (
    <svg {...base} {...props} aria-hidden>
      <path d="M9 3v2M15 3v2M9 19v2M15 19v2M3 9h2M3 15h2M19 9h2M19 15h2" />
      <path d="M12 8l-3 3 3 3 3-3-3-3z" fill="currentColor" stroke="none" />
    </svg>
  );
}
