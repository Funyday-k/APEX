import type { PlotRegionsPayload } from '../store/useStore';

/** Scale region bboxes to match actual loaded image pixel dimensions. */
export function normalizeRegionsToImage(
  regions: PlotRegionsPayload | null,
  targetWidth: number,
  targetHeight: number
): PlotRegionsPayload | null {
  if (!regions?.regions?.length) return regions;
  const srcW = regions.image_width || targetWidth;
  const srcH = regions.image_height || targetHeight;
  if (srcW <= 0 || srcH <= 0) {
    return {
      ...regions,
      image_width: targetWidth,
      image_height: targetHeight,
    };
  }
  if (srcW === targetWidth && srcH === targetHeight) {
    return { ...regions, image_width: targetWidth, image_height: targetHeight };
  }
  const sx = targetWidth / srcW;
  const sy = targetHeight / srcH;
  return {
    ...regions,
    image_width: targetWidth,
    image_height: targetHeight,
    regions: regions.regions.map((r) => ({
      ...r,
      bbox: {
        x0: Math.round(r.bbox.x0 * sx),
        y0: Math.round(r.bbox.y0 * sy),
        x1: Math.round(r.bbox.x1 * sx),
        y1: Math.round(r.bbox.y1 * sy),
      },
    })),
  };
}

/** Map natural-pixel bbox to Konva canvas coordinates (fitted display size). */
export function bboxToCanvasRect(
  bbox: { x0: number; y0: number; x1: number; y1: number },
  naturalWidth: number,
  naturalHeight: number,
  canvasWidth: number,
  canvasHeight: number
) {
  const sx = canvasWidth / Math.max(1, naturalWidth);
  const sy = canvasHeight / Math.max(1, naturalHeight);
  return {
    x: bbox.x0 * sx,
    y: bbox.y0 * sy,
    width: (bbox.x1 - bbox.x0) * sx,
    height: (bbox.y1 - bbox.y0) * sy,
  };
}

/** Map Konva display rect back to natural-pixel bbox. */
export function canvasRectToBbox(
  rect: { x: number; y: number; width: number; height: number },
  naturalWidth: number,
  naturalHeight: number,
  canvasWidth: number,
  canvasHeight: number
) {
  const sx = Math.max(1, naturalWidth) / Math.max(1, canvasWidth);
  const sy = Math.max(1, naturalHeight) / Math.max(1, canvasHeight);
  const x0 = Math.round(rect.x * sx);
  const y0 = Math.round(rect.y * sy);
  const x1 = Math.round((rect.x + rect.width) * sx);
  const y1 = Math.round((rect.y + rect.height) * sy);
  return {
    x0: Math.max(0, Math.min(x0, x1)),
    y0: Math.max(0, Math.min(y0, y1)),
    x1: Math.min(naturalWidth, Math.max(x0, x1)),
    y1: Math.min(naturalHeight, Math.max(y0, y1)),
  };
}

export const REGION_KINDS = [
  'plot_area',
  'legend',
  'legend_marker',
  'x_axis',
  'y_axis',
  'x_tick_labels',
  'y_tick_labels',
  'title',
  'colorbar',
  'other_text',
] as const;
