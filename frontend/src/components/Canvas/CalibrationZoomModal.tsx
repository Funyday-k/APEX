import React, { type FormEvent, useEffect, useRef } from 'react';
import { useT } from '../../i18n/useT';
import type { ImageGeometry, Pixel } from '../../store/useStore';
import { nudgeNatural } from '../../utils/canvasCoords';

type Props = {
  open: boolean;
  image: HTMLImageElement;
  geometry: ImageGeometry;
  natural: Pixel;
  axis: 'x' | 'y';
  value: string;
  onValueChange: (v: string) => void;
  onNaturalChange: (p: Pixel) => void;
  onConfirm: () => void;
  onCancel: () => void;
};

const MODAL_SIZE = 320;
const ZOOM = 8;

export const CalibrationZoomModal: React.FC<Props> = ({
  open,
  image,
  geometry,
  natural,
  axis,
  value,
  onValueChange,
  onNaturalChange,
  onConfirm,
  onCancel,
}) => {
  const { t } = useT();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!open) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const natW = geometry.natural.x;
    const natH = geometry.natural.y;
    const halfWindow = MODAL_SIZE / ZOOM / 2;
    const sx = Math.max(0, natural.x - halfWindow);
    const sy = Math.max(0, natural.y - halfWindow);
    const sw = Math.min(halfWindow * 2, natW - sx);
    const sh = Math.min(halfWindow * 2, natH - sy);

    ctx.clearRect(0, 0, MODAL_SIZE, MODAL_SIZE);
    ctx.imageSmoothingEnabled = false;
    if (sw > 0 && sh > 0) {
      ctx.drawImage(image, sx, sy, sw, sh, 0, 0, MODAL_SIZE, MODAL_SIZE);
    }

    const localX = sw > 0 ? ((natural.x - sx) / sw) * MODAL_SIZE : MODAL_SIZE / 2;
    const localY = sh > 0 ? ((natural.y - sy) / sh) * MODAL_SIZE : MODAL_SIZE / 2;
    ctx.strokeStyle = axis === 'x' ? '#e53935' : '#1e88e5';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(localX, 0);
    ctx.lineTo(localX, MODAL_SIZE);
    ctx.moveTo(0, localY);
    ctx.lineTo(MODAL_SIZE, localY);
    ctx.stroke();
    ctx.strokeStyle = '#fff';
    ctx.beginPath();
    ctx.arc(localX, localY, 5, 0, Math.PI * 2);
    ctx.stroke();
  }, [open, image, geometry, natural, axis]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
        return;
      }
      const step = e.shiftKey ? 5 : 1;
      let dx = 0;
      let dy = 0;
      if (e.key === 'ArrowLeft') dx = -step;
      else if (e.key === 'ArrowRight') dx = step;
      else if (e.key === 'ArrowUp') dy = -step;
      else if (e.key === 'ArrowDown') dy = step;
      else if (e.key === 'Enter' && value.trim()) {
        e.preventDefault();
        onConfirm();
        return;
      } else return;
      e.preventDefault();
      onNaturalChange(nudgeNatural(natural, dx, dy, geometry));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, natural, geometry, value, onCancel, onConfirm, onNaturalChange]);

  if (!open) return null;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    onConfirm();
  };

  return (
    <div className="calibration-modal-backdrop" role="dialog" aria-modal="true">
      <div className="calibration-modal">
        <h3>{t('calibrationModalTitle')}</h3>
        <p className="hint">{t('calibMagnifierHint')}</p>
        <div className="calibration-modal-canvas-wrap">
          <canvas ref={canvasRef} width={MODAL_SIZE} height={MODAL_SIZE} />
          <div className="calibration-modal-coords">
            ({Math.round(natural.x)}, {Math.round(natural.y)})
          </div>
        </div>
        <form onSubmit={submit}>
          <label>
            {t('calibInputLabel', { axis: axis.toUpperCase() })}
            <input
              autoFocus
              value={value}
              onChange={(e) => onValueChange(e.target.value)}
              placeholder="0"
              inputMode="decimal"
            />
          </label>
          <div className="btn-row">
            <button type="submit" className="btn-primary">
              {t('calibConfirm')}
            </button>
            <button type="button" className="btn-muted" onClick={onCancel}>
              {t('calibCancel')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
