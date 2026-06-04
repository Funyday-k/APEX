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
