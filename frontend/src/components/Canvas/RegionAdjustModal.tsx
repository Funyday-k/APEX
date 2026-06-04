import React, { useEffect, useRef, useState } from 'react';
import { useT } from '../../i18n/useT';
import type { TranslationKey } from '../../i18n/translations';
import type { ImageGeometry } from '../../store/useStore';
import {
  clampBBox,
  nudgeRegionBBox,
  type RegionAdjustTarget,
} from '../../utils/regionBBox';

type BBox = { x0: number; y0: number; x1: number; y1: number };

type Props = {
  open: boolean;
  image: HTMLImageElement;
  geometry: ImageGeometry;
  bbox: BBox;
  onBBoxChange: (bbox: BBox) => void;
  onClose: () => void;
};

const MODAL_SIZE = 360;
const ZOOM = 6;

const TARGETS: { id: RegionAdjustTarget; labelKey: TranslationKey }[] = [
  { id: 'move', labelKey: 'regionTargetMove' },
  { id: 'left', labelKey: 'regionTargetLeft' },
  { id: 'right', labelKey: 'regionTargetRight' },
  { id: 'top', labelKey: 'regionTargetTop' },
  { id: 'bottom', labelKey: 'regionTargetBottom' },
  { id: 'tl', labelKey: 'regionTargetTL' },
  { id: 'tr', labelKey: 'regionTargetTR' },
  { id: 'bl', labelKey: 'regionTargetBL' },
  { id: 'br', labelKey: 'regionTargetBR' },
];

export function RegionAdjustModal({
  open,
  image,
  geometry,
  bbox,
  onBBoxChange,
  onClose,
}: Props) {
  const { t } = useT();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [local, setLocal] = useState(bbox);
  const [target, setTarget] = useState<RegionAdjustTarget>('move');

  useEffect(() => {
    if (open) setLocal(bbox);
  }, [open, bbox]);

  const maxW = geometry.natural.x;
  const maxH = geometry.natural.y;

  useEffect(() => {
    if (!open) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const cx = (local.x0 + local.x1) / 2;
    const cy = (local.y0 + local.y1) / 2;
    const half = MODAL_SIZE / ZOOM / 2;
    const sx = Math.max(0, cx - half);
    const sy = Math.max(0, cy - half);
    const sw = Math.min(half * 2, maxW - sx);
    const sh = Math.min(half * 2, maxH - sy);

    ctx.clearRect(0, 0, MODAL_SIZE, MODAL_SIZE);
    ctx.imageSmoothingEnabled = false;
    if (sw > 0 && sh > 0) {
      ctx.drawImage(image, sx, sy, sw, sh, 0, 0, MODAL_SIZE, MODAL_SIZE);
    }

    const toLocal = (nx: number, ny: number) => ({
      x: sw > 0 ? ((nx - sx) / sw) * MODAL_SIZE : MODAL_SIZE / 2,
      y: sh > 0 ? ((ny - sy) / sh) * MODAL_SIZE : MODAL_SIZE / 2,
    });
    const p0 = toLocal(local.x0, local.y0);
    const p1 = toLocal(local.x1, local.y1);
    const rx = Math.min(p0.x, p1.x);
    const ry = Math.min(p0.y, p1.y);
    const rw = Math.abs(p1.x - p0.x);
    const rh = Math.abs(p1.y - p0.y);

    ctx.strokeStyle = '#1677ff';
    ctx.lineWidth = 2;
    ctx.strokeRect(rx, ry, rw, rh);
    ctx.fillStyle = 'rgba(22,119,255,0.12)';
    ctx.fillRect(rx, ry, rw, rh);

    const corners: [number, number][] = [
      [rx, ry],
      [rx + rw, ry],
      [rx, ry + rh],
      [rx + rw, ry + rh],
    ];
    ctx.fillStyle = '#1677ff';
    for (const [px, py] of corners) {
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [open, image, local, maxW, maxH]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      const step = e.shiftKey ? 5 : 1;
      let dx = 0;
      let dy = 0;
      if (e.key === 'ArrowLeft') dx = -step;
      else if (e.key === 'ArrowRight') dx = step;
      else if (e.key === 'ArrowUp') dy = -step;
      else if (e.key === 'ArrowDown') dy = step;
      else if (e.key === 'Enter') {
        e.preventDefault();
        onBBoxChange(clampBBox(local, maxW, maxH));
        onClose();
        return;
      } else return;
      e.preventDefault();
      setLocal((b) => nudgeRegionBBox(b, target, dx, dy, maxW, maxH));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, local, target, maxW, maxH, onBBoxChange, onClose]);

  if (!open) return null;

  return (
    <div className="calibration-modal-backdrop" role="dialog" aria-modal="true">
      <div className="calibration-modal region-adjust-modal">
        <h3>{t('regionAdjustTitle')}</h3>
        <p className="hint">{t('regionAdjustHint')}</p>
        <div className="region-target-row">
          {TARGETS.map((tg) => (
            <button
              key={tg.id}
              type="button"
              className={`btn-muted btn-sm${target === tg.id ? ' active' : ''}`}
              onClick={() => setTarget(tg.id)}
            >
              {t(tg.labelKey)}
            </button>
          ))}
        </div>
        <div className="calibration-modal-canvas-wrap">
          <canvas ref={canvasRef} width={MODAL_SIZE} height={MODAL_SIZE} />
          <div className="calibration-modal-coords">
            ({local.x0}, {local.y0}) – ({local.x1}, {local.y1})
          </div>
        </div>
        <div className="btn-row">
          <button
            type="button"
            className="btn-primary"
            onClick={() => {
              onBBoxChange(clampBBox(local, maxW, maxH));
              onClose();
            }}
          >
            {t('calibConfirm')}
          </button>
          <button type="button" className="btn-muted" onClick={onClose}>
            {t('calibCancel')}
          </button>
        </div>
      </div>
    </div>
  );
}
