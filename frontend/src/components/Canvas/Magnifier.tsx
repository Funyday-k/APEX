import React, { useEffect, useRef } from 'react';
import type { ImageGeometry, Pixel } from '../../store/useStore';

type Props = {
  image: HTMLImageElement;
  naturalPoint: Pixel;
  geometry: ImageGeometry;
  /** Screen position relative to stage shell (px). */
  screenPos: Pixel;
  zoom?: number;
  size?: number;
  axis?: 'x' | 'y';
};

const DEFAULT_ZOOM = 6;
const DEFAULT_SIZE = 140;

export const Magnifier: React.FC<Props> = ({
  image,
  naturalPoint,
  geometry,
  screenPos,
  zoom = DEFAULT_ZOOM,
  size = DEFAULT_SIZE,
  axis,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const natW = geometry.natural.x;
    const natH = geometry.natural.y;
    const halfWindow = size / zoom / 2;

    const sx = Math.max(0, naturalPoint.x - halfWindow);
    const sy = Math.max(0, naturalPoint.y - halfWindow);
    const sw = Math.min(halfWindow * 2, natW - sx);
    const sh = Math.min(halfWindow * 2, natH - sy);

    ctx.clearRect(0, 0, size, size);
    ctx.imageSmoothingEnabled = false;
    if (sw > 0 && sh > 0) {
      ctx.drawImage(image, sx, sy, sw, sh, 0, 0, size, size);
    }

    const localX = sw > 0 ? ((naturalPoint.x - sx) / sw) * size : size / 2;
    const localY = sh > 0 ? ((naturalPoint.y - sy) / sh) * size : size / 2;

    ctx.strokeStyle = axis === 'x' ? '#e53935' : axis === 'y' ? '#1e88e5' : '#333';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(localX, 0);
    ctx.lineTo(localX, size);
    ctx.moveTo(0, localY);
    ctx.lineTo(size, localY);
    ctx.stroke();

    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.arc(localX, localY, 3, 0, Math.PI * 2);
    ctx.stroke();
  }, [image, naturalPoint, geometry, size, zoom, axis]);

  const shellWidth = geometry.display.x;
  const left = Math.min(screenPos.x + 16, shellWidth - size - 8);
  const top = Math.max(8, screenPos.y - size - 16);

  return (
    <div
      className="calibration-magnifier"
      style={{ left, top, width: size, height: size }}
      aria-hidden
    >
      <canvas ref={canvasRef} width={size} height={size} />
      <div className="calibration-magnifier-coords">
        ({Math.round(naturalPoint.x)}, {Math.round(naturalPoint.y)})
      </div>
    </div>
  );
};
