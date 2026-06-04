import { describe, expect, it } from 'vitest';
import {
  clampToDisplay,
  containerToDisplay,
  displayToContainer,
  displayToNatural,
  mapPointBetweenSizes,
  naturalToDisplay,
  nudgeNatural,
  snapNatural,
} from './canvasCoords';
import type { ImageGeometry } from '../store/useStore';

const geometry: ImageGeometry = {
  natural: { x: 2000, y: 1000 },
  display: { x: 900, y: 450 },
};

describe('canvasCoords', () => {
  it('maps display to natural and back', () => {
    const display = { x: 450, y: 225 };
    const natural = displayToNatural(display, geometry);
    expect(natural.x).toBeCloseTo(1000, 5);
    expect(natural.y).toBeCloseTo(500, 5);
    const back = naturalToDisplay(natural, geometry);
    expect(back.x).toBeCloseTo(display.x, 5);
    expect(back.y).toBeCloseTo(display.y, 5);
  });

  it('applies stage transform consistently', () => {
    const transform = { scale: 2, offsetX: 10, offsetY: 20 };
    const display = { x: 100, y: 50 };
    const container = displayToContainer(display, transform);
    expect(container.x).toBe(210);
    expect(container.y).toBe(120);
    const back = containerToDisplay(container.x, container.y, transform);
    expect(back.x).toBeCloseTo(display.x, 5);
    expect(back.y).toBeCloseTo(display.y, 5);
  });

  it('clamps display coordinates', () => {
    const clamped = clampToDisplay({ x: 999, y: -5 }, geometry.display);
    expect(clamped.x).toBe(900);
    expect(clamped.y).toBe(0);
  });

  it('nudges natural pixels within bounds', () => {
    const start = { x: 10, y: 10 };
    const moved = nudgeNatural(start, -20, 0, geometry);
    expect(moved.x).toBe(0);
    expect(moved.y).toBe(10);
    expect(snapNatural({ x: 10.6, y: 20.4 })).toEqual({ x: 11, y: 20 });
  });

  it('handles zero-width source in mapPointBetweenSizes', () => {
    expect(mapPointBetweenSizes({ x: 5, y: 7 }, { x: 0, y: 100 }, { x: 200, y: 100 })).toEqual({
      x: 5,
      y: 7,
    });
  });
});
