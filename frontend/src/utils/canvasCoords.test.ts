import { describe, expect, it } from 'vitest';
import { clampStagePos, zoomAtPoint } from './canvasCoords';

describe('clampStagePos', () => {
  it('keeps content within viewport when smaller than viewport', () => {
    const pos = clampStagePos({ x: -50, y: -30 }, 1, { w: 400, h: 300 }, { w: 200, h: 150 });
    expect(pos.x).toBe(0);
    expect(pos.y).toBe(0);
  });

  it('allows panning when content larger than viewport', () => {
    const pos = clampStagePos({ x: -500, y: -400 }, 2, { w: 400, h: 300 }, { w: 300, h: 200 });
    expect(pos.x).toBeGreaterThanOrEqual(400 - 600);
    expect(pos.y).toBeGreaterThanOrEqual(300 - 400);
  });
});

describe('zoomAtPoint', () => {
  it('zooms toward pointer', () => {
    const { scale, pos } = zoomAtPoint(1, { x: 0, y: 0 }, { x: 100, y: 100 }, 1.2);
    expect(scale).toBeCloseTo(1.2);
    expect(pos.x).toBeCloseTo(-20);
    expect(pos.y).toBeCloseTo(-20);
  });
});
