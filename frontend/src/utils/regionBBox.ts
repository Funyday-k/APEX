export type BBox = { x0: number; y0: number; x1: number; y1: number };

export type RegionAdjustTarget =
  | 'move'
  | 'left'
  | 'right'
  | 'top'
  | 'bottom'
  | 'tl'
  | 'tr'
  | 'bl'
  | 'br';

export function normalizeBBox(b: BBox): BBox {
  return {
    x0: Math.min(b.x0, b.x1),
    y0: Math.min(b.y0, b.y1),
    x1: Math.max(b.x0, b.x1),
    y1: Math.max(b.y0, b.y1),
  };
}

export function clampBBox(b: BBox, maxW: number, maxH: number, minSize = 4): BBox {
  const n = normalizeBBox(b);
  let { x0, y0, x1, y1 } = n;
  if (x1 - x0 < minSize) x1 = x0 + minSize;
  if (y1 - y0 < minSize) y1 = y0 + minSize;
  x0 = Math.max(0, Math.min(x0, maxW - minSize));
  y0 = Math.max(0, Math.min(y0, maxH - minSize));
  x1 = Math.max(minSize, Math.min(x1, maxW));
  y1 = Math.max(minSize, Math.min(y1, maxH));
  return normalizeBBox({ x0, y0, x1, y1 });
}

/** Nudge region bbox by target (natural pixels). */
export function nudgeRegionBBox(
  bbox: BBox,
  target: RegionAdjustTarget,
  dx: number,
  dy: number,
  maxW: number,
  maxH: number
): BBox {
  let { x0, y0, x1, y1 } = normalizeBBox(bbox);
  switch (target) {
    case 'move':
      x0 += dx;
      x1 += dx;
      y0 += dy;
      y1 += dy;
      break;
    case 'left':
      x0 += dx;
      break;
    case 'right':
      x1 += dx;
      break;
    case 'top':
      y0 += dy;
      break;
    case 'bottom':
      y1 += dy;
      break;
    case 'tl':
      x0 += dx;
      y0 += dy;
      break;
    case 'tr':
      x1 += dx;
      y0 += dy;
      break;
    case 'bl':
      x0 += dx;
      y1 += dy;
      break;
    case 'br':
      x1 += dx;
      y1 += dy;
      break;
    default:
      break;
  }
  return clampBBox({ x0, y0, x1, y1 }, maxW, maxH);
}

/** Center stage position so content at scale fits in viewport. */
export function centerStagePos(
  scale: number,
  viewport: { w: number; h: number },
  content: { w: number; h: number }
): { x: number; y: number } {
  const sw = content.w * scale;
  const sh = content.h * scale;
  return {
    x: Math.max(0, (viewport.w - sw) / 2),
    y: Math.max(0, (viewport.h - sh) / 2),
  };
}
