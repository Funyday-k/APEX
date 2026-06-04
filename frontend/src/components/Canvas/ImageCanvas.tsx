import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Image as KonvaImage, Layer, Stage } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import type Konva from 'konva';
import useImage from 'use-image';
import { useT } from '../../i18n/useT';
import { fitImageSize, useStore } from '../../store/useStore';
import {
  containerToDisplay,
  displayToNaturalClamped,
  nudgeNatural,
  type StageTransform,
} from '../../utils/canvasCoords';
import { CalibrationLayer } from './CalibrationLayer';
import { CalibrationZoomModal } from './CalibrationZoomModal';
import { DataPointLayer } from './DataPointLayer';
import { Magnifier } from './Magnifier';
import { RegionOverlay } from './RegionOverlay';

type Props = { mode: 'calibrating' | 'extracted' | 'preview' };

type PendingPoint = {
  axis: 'x' | 'y';
  natural: { x: number; y: number };
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
    selectedCalib,
    setSelectedCalib,
    updateCalibPoint,
  } = useStore();
  const { t } = useT();
  const [image] = useImage(imageUrl || '', 'anonymous');
  const [scale, setScale] = useState(1);
  const [stagePos, setStagePos] = useState({ x: 0, y: 0 });
  const [pendingPoint, setPendingPoint] = useState<PendingPoint | null>(null);
  const [hoverNatural, setHoverNatural] = useState<{ x: number; y: number } | null>(null);
  const [hoverScreen, setHoverScreen] = useState<{ x: number; y: number } | null>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const shellRef = useRef<HTMLDivElement>(null);

  const transform: StageTransform = { scale, offsetX: stagePos.x, offsetY: stagePos.y };

  const handleWheel = (e: KonvaEventObject<WheelEvent>) => {
    if (mode === 'calibrating') return;
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

  const pointerToNatural = useCallback(
    (evt: { offsetX: number; offsetY: number }) => {
      if (!imageGeometry) return null;
      const display = containerToDisplay(evt.offsetX, evt.offsetY, transform);
      return displayToNaturalClamped(display, imageGeometry);
    },
    [imageGeometry, transform]
  );

  const handleStageClick = (evt: KonvaEventObject<MouseEvent>) => {
    if (mode !== 'calibrating' || !shellRef.current || pendingPoint) return;
    const stage = evt.target.getStage();
    if (!stage || evt.target !== stage) return;
    const shellRect = shellRef.current.getBoundingClientRect();
    const screen = {
      x: evt.evt.clientX - shellRect.left,
      y: evt.evt.clientY - shellRect.top,
    };
    const natural = pointerToNatural({ offsetX: screen.x, offsetY: screen.y });
    if (!natural) return;
    setSelectedCalib(null);
    setPendingPoint({ axis: calibAxis, natural, value: '' });
  };

  const confirmPending = () => {
    if (!pendingPoint) return;
    const num = Number.parseFloat(pendingPoint.value);
    if (!Number.isFinite(num)) return;
    addCalibPoint({
      pixel: pendingPoint.natural,
      data: pendingPoint.axis === 'x' ? { x: num, y: 0 } : { x: 0, y: num },
    });
    setPendingPoint(null);
  };

  useEffect(() => {
    if (mode !== 'calibrating' || !selectedCalib || !imageGeometry || pendingPoint) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      const step = e.shiftKey ? 5 : 1;
      let dx = 0;
      let dy = 0;
      if (e.key === 'ArrowLeft') dx = -step;
      else if (e.key === 'ArrowRight') dx = step;
      else if (e.key === 'ArrowUp') dy = -step;
      else if (e.key === 'ArrowDown') dy = step;
      else if (e.key === 'Escape') {
        setSelectedCalib(null);
        return;
      } else return;
      e.preventDefault();
      const { axis, index } = selectedCalib;
      const refs = axis === 'x' ? useStore.getState().xRefs : useStore.getState().yRefs;
      const cur = refs[index];
      if (!cur) return;
      const next = nudgeNatural(cur.pixel, dx, dy, imageGeometry);
      updateCalibPoint(axis, index, next);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [mode, selectedCalib, imageGeometry, pendingPoint, setSelectedCalib, updateCalibPoint]);

  const onShellMouseMove = (e: React.MouseEvent) => {
    if (mode !== 'calibrating' || !shellRef.current || !imageGeometry) return;
    const rect = shellRef.current.getBoundingClientRect();
    const screen = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    const natural = pointerToNatural({ offsetX: screen.x, offsetY: screen.y });
    setHoverScreen(screen);
    setHoverNatural(natural);
  };

  if (!imageUrl) return <div className="canvas-placeholder">{t('canvasUploadFirst')}</div>;
  if (!image) return <div className="canvas-placeholder">{t('canvasLoading')}</div>;

  const natural = {
    x: image.naturalWidth || image.width,
    y: image.naturalHeight || image.height,
  };
  const display = fitImageSize(natural.x, natural.y);
  const w = display.x;
  const h = display.y;
  const geometry =
    imageGeometry ||
    ({
      natural,
      display: { x: w, y: h },
    } as const);

  const showOverlay =
    showRegionOverlay && regions?.regions?.length && (mode === 'preview' || mode === 'calibrating');

  return (
    <div
      ref={shellRef}
      className={`konva-stage-shell${mode === 'calibrating' ? ' calibrating' : ''}`}
      style={{ width: w, height: h }}
      onMouseMove={onShellMouseMove}
      onMouseLeave={() => {
        setHoverNatural(null);
        setHoverScreen(null);
      }}
    >
      <Stage
        ref={stageRef}
        width={w}
        height={h}
        scaleX={scale}
        scaleY={scale}
        x={stagePos.x}
        y={stagePos.y}
        onWheel={handleWheel}
        draggable={mode === 'extracted'}
        onDragEnd={(e) => setStagePos({ x: e.target.x(), y: e.target.y() })}
        onClick={handleStageClick}
        style={{ cursor: mode === 'calibrating' ? 'crosshair' : 'default' }}
      >
        <Layer listening={false}>
          <KonvaImage image={image} width={w} height={h} listening={false} />
        </Layer>
        {showOverlay && (
          <Layer listening={false}>
            <RegionOverlay
              regions={regions!.regions}
              naturalWidth={natural.x}
              naturalHeight={natural.y}
              canvasWidth={w}
              canvasHeight={h}
            />
          </Layer>
        )}
        {mode === 'calibrating' && (
          <CalibrationLayer
            pendingPoint={pendingPoint}
            interactive
            geometry={geometry}
            onSelectRef={(axis, index) => setSelectedCalib({ axis, index })}
            onDragRef={(axis, index, nat) => updateCalibPoint(axis, index, nat)}
          />
        )}
        {mode === 'extracted' && <DataPointLayer />}
      </Stage>

      {mode === 'calibrating' &&
        hoverNatural &&
        hoverScreen &&
        !pendingPoint &&
        imageGeometry && (
          <Magnifier
            image={image}
            naturalPoint={hoverNatural}
            geometry={imageGeometry}
            screenPos={hoverScreen}
            axis={calibAxis}
          />
        )}

      {pendingPoint && imageGeometry && (
        <CalibrationZoomModal
          open
          image={image}
          geometry={imageGeometry}
          natural={pendingPoint.natural}
          axis={pendingPoint.axis}
          value={pendingPoint.value}
          onValueChange={(value) => setPendingPoint((p) => (p ? { ...p, value } : p))}
          onNaturalChange={(natural) => setPendingPoint((p) => (p ? { ...p, natural } : p))}
          onConfirm={confirmPending}
          onCancel={() => setPendingPoint(null)}
        />
      )}
    </div>
  );
};
