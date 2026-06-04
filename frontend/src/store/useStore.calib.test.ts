import { describe, expect, it } from 'vitest';
import { buildCalibration } from './useStore';

describe('buildCalibration', () => {
  it('builds config when four refs present', () => {
    const cal = buildCalibration(
      [
        { pixel: { x: 10, y: 100 }, data: { x: 0, y: 0 } },
        { pixel: { x: 200, y: 100 }, data: { x: 1, y: 0 } },
      ],
      [
        { pixel: { x: 10, y: 80 }, data: { x: 0, y: 1 } },
        { pixel: { x: 10, y: 20 }, data: { x: 0, y: 0 } },
      ],
      'linear',
      'linear'
    );
    expect(cal).not.toBeNull();
    expect(cal!.x_axis.ref1.data.x).toBe(0);
    expect(cal!.y_axis.scale).toBe('linear');
  });
});
