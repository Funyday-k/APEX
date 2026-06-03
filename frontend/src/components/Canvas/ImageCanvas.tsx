import React, { type FormEvent, useEffect, useRef, useState } from 'react';
import { Image as KonvaImage, Layer, Stage } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import useImage from 'use-image';
import { useT } from '../../i18n/useT';
import { fitImageSize, useStore } from '../../store/useStore';
import { CalibrationLayer } from './CalibrationLayer';
import { DataPointLayer } from './DataPointLayer';
import { RegionOverlay } from './RegionOverlay';

type Props = { mode: 'calibrating' | 'extracted' };
type PendingPoint = {
  axis: 'x' | 'y';
  pixel: { x: number; y: number };
  screen: { x: number; y: number };
  value: string;
};

export const ImageCanvas: React.FC<Props> = ({ mode }) => {
  const {
    imageUrl,
    calibAxis,
    addCalibPoint,
    setImageGeometry,
    regions,
    imageGeometry,
    showRegionOverlay,
  } = useStore();
  const { t } = useT();
  const [image] = useImage(imageUrl || '', 'anonymous');
  const [scale, setScale] = useState(1);
  const [pendingPoint, setPendingPoint] = useState<PendingPoint | null>(null);
  const stageRef = useRef(null);

  const handleWheel = (e: KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    setScale((s) => Math.min(4, Math.max(0.2, e.evt.deltaY > 0 ? s / 1.1 : s * 1.1)));
  };

  useEffect(() => {
    if (!image) return;
    setImageGeometry({
      x: image.naturalWidth || image.width,
      y: image.naturalHeight || image.height,
    });
  }, [image, setImageGeometry]);

  if (!imageUrl) return <div className="canvas-placeholder">{t('canvasUploadFirst')}</div>;
  if (!image) return <div className="canvas-placeholder">{t('canvasLoading')}</div>;

  const natural = {
    x: image.naturalWidth || image.width,
    y: image.naturalHeight || image.height,
  };
  const display = fitImageSize(natural.x, natural.y);
  const w = display.x;
  const h = display.y;

  const handleCalibrationClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const screen = {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
    const pixel = {
      x: Math.min(w, Math.max(0, screen.x / scale)),
      y: Math.min(h, Math.max(0, screen.y / scale)),
    };
    setPendingPoint({ axis: calibAxis, pixel, screen, value: '' });
  };

  const handleCalibrationSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!pendingPoint) return;
    const num = Number.parseFloat(pendingPoint.value);
    if (!Number.isFinite(num)) return;

    addCalibPoint({
      pixel: pendingPoint.pixel,
      data: pendingPoint.axis === 'x' ? { x: num, y: 0 } : { x: 0, y: num },
    });
    setPendingPoint(null);
  };

  return (
    <div className="konva-stage-shell" style={{ width: w, height: h }}>
      <Stage
        ref={stageRef}
        width={w}
        height={h}
        scaleX={scale}
        scaleY={scale}
        onWheel={handleWheel}
        draggable={mode !== 'calibrating'}
      >
        <Layer listening={false}>
          <KonvaImage image={image} width={w} height={h} listening={false} />
        </Layer>
        {showRegionOverlay && regions?.regions?.length && imageGeometry && (
          <Layer listening={false}>
            <RegionOverlay regions={regions.regions} geometry={imageGeometry} />
          </Layer>
        )}
        {mode === 'calibrating' && <CalibrationLayer />}
        {mode === 'extracted' && <DataPointLayer />}
      </Stage>

      {mode === 'calibrating' && (
        <div
          className="calibration-click-overlay"
          onClick={handleCalibrationClick}
          role="button"
          tabIndex={0}
          aria-label={t('calibrationClickArea')}
        />
      )}

      {pendingPoint && (
        <form
          className="calibration-popover"
          style={{
            left: Math.min(w - 220, Math.max(8, pendingPoint.screen.x + 10)),
            top: Math.min(h - 98, Math.max(8, pendingPoint.screen.y + 10)),
          }}
          onClick={(event) => event.stopPropagation()}
          onSubmit={handleCalibrationSubmit}
        >
          <label>
            {t('calibInputLabel', { axis: pendingPoint.axis.toUpperCase() })}
            <input
              autoFocus
              value={pendingPoint.value}
              onChange={(event) =>
                setPendingPoint((point) =>
                  point ? { ...point, value: event.target.value } : point
                )
              }
              placeholder="0"
              inputMode="decimal"
            />
          </label>
          <div className="btn-row compact">
            <button type="submit" className="btn-primary">
              {t('calibConfirm')}
            </button>
            <button
              type="button"
              className="btn-muted"
              onClick={() => setPendingPoint(null)}
            >
              {t('calibCancel')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
