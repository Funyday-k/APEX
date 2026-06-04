import { describe, expect, it } from 'vitest';
import { centerStagePos, clampBBox, nudgeRegionBBox } from './regionBBox';

describe('nudgeRegionBBox', () => {
  it('moves whole box', () => {
    const b = { x0: 10, y0: 20, x1: 50, y1: 60 };
    const next = nudgeRegionBBox(b, 'move', 5, 3, 200, 200);
    expect(next.x0).toBe(15);
    expect(next.y0).toBe(23);
  });

  it('expands right edge', () => {
    const b = { x0: 10, y0: 20, x1: 50, y1: 60 };
    const next = nudgeRegionBBox(b, 'right', 4, 0, 200, 200);
    expect(next.x1).toBe(54);
    expect(next.x0).toBe(10);
  });
});

describe('centerStagePos', () => {
  it('centers content in viewport', () => {
    const pos = centerStagePos(1, { w: 400, h: 300 }, { w: 200, h: 100 });
    expect(pos.x).toBe(100);
    expect(pos.y).toBe(100);
  });
});

describe('clampBBox', () => {
  it('enforces minimum size', () => {
    const b = clampBBox({ x0: 0, y0: 0, x1: 1, y1: 1 }, 100, 100);
    expect(b.x1 - b.x0).toBeGreaterThanOrEqual(4);
  });
});
