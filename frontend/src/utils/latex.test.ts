import { describe, expect, it } from 'vitest';
import { hasLatex, latexToPlain } from './latex';

describe('latex utils', () => {
  it('strips simple latex', () => {
    expect(latexToPlain('$m_\\chi$')).toContain('m');
  });

  it('detects latex markers', () => {
    expect(hasLatex('$r/R_{\\odot}$')).toBe(true);
    expect(hasLatex('plain text')).toBe(false);
  });
});
