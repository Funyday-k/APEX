import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Image as KonvaImage, Layer, Stage } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import type Konva from 'konva';
import useImage from 'use-image';
import { useT } from '../../i18n/useT';
import { fitImageSize, useStore } from '../../store/useStore';
import {
  clampStagePos,
  containerToDisplay,
  displayToNaturalClamped,
  nudgeNatural,
  zoomAtPoint,
  type StageTransform,
} from '../../utils/canvasCoords';
import { centerStagePos } from '../../utils/regionBBox';
import { CalibrationLayer } from './CalibrationLayer';
import { CalibrationZoomModal } from './CalibrationZoomModal';
import { CanvasToolbar } from './CanvasToolbar';
import { DataPointLayer } from './DataPointLayer';
import { Magnifier } from './Magnifier';
import { RegionOverlay } from './RegionOverlay';

type Props = { mode: 'calibrating' | 'extracted' | 'preview' };

type PendingPoint = {
  axis: 'x' | 'y';
  natural: { x: number; y: number };
  value: string;
};

const MIN_SCALE = 1;
const MAX_SCALE = 4;

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
    selectedRegionIndex,
    setSelectedRegionIndex,
    updateRegion,
    canvasScale,
    canvasStagePos,
    canvasViewport,
    canvasPanMode,
    setCanvasScale,
    setCanvasStagePos,
    setCanvasViewport,
    initCanvasView,
  } = useStore();
  const { t } = useT();
  const [image] = useImage(imageUrl || '', 'anonymous');
  const [pendingPoint, setPendingPoint] = useState<PendingPoint | null>(null);
  const [hoverNatural, setHoverNatural] = useState<{ x: number; y: number } | null>(null);
  const [hoverScreen, setHoverScreen] = useState<{ x: number; y: number } | null>(null);
  const [spacePan, setSpacePan] = useState(false);
  const stageRef = useRef<Konva.Stage>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasInitedRef = useRef(false);

  const panActive = canvasPanMode || spacePan;

  const transform: StageTransform = {
    scale: canvasScale,
    offsetX: canvasStagePos.x,
    offsetY: canvasStagePos.y,
  };

  const clampPos = useCallback(
    (pos: { x: number; y: number }, scale: number, cw: number, ch: number) =>
      clampStagePos(pos, scale, canvasViewport, { w: cw, h: ch }),
    [canvasViewport]
  );

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setCanvasViewport(el.clientWidth || 900, el.clientHeight || 650);
    });
    ro.observe(el);
    setCanvasViewport(el.clientWidth || 900, el.clientHeight || 650);
    return () => ro.disconnect();
  }, [setCanvasViewport]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !e.repeat) {
        if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
          return;
        }
        e.preventDefault();
        setSpacePan(true);
      }
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') setSpacePan(false);
    };
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
    };
  }, []);

  const handleWheel = (e: KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    const factor = e.evt.deltaY > 0 ? 1 / 1.1 : 1.1;
    let { scale, pos } = zoomAtPoint(
      canvasScale,
      canvasStagePos,
      pointer,
      factor,
      MIN_SCALE,
      MAX_SCALE
    );
    if (factor < 1 && scale < MIN_SCALE) {
      scale = MIN_SCALE;
      const display = fitImageSize(
        image?.naturalWidth || image?.width || 1,
        image?.naturalHeight || image?.height || 1
      );
      pos = centerStagePos(scale, canvasViewport, { w: display.x, h: display.y });
    }
    setCanvasScale(scale);
    const display = fitImageSize(
      image?.naturalWidth || image?.width || 1,
      image?.naturalHeight || image?.height || 1
    );
    setCanvasStagePos(clampPos(pos, scale, display.x, display.y));
  };

  useEffect(() => {
    if (!image) return;
    setImageGeometry({
      x: image.naturalWidth || image.width,
      y: image.naturalHeight || image.height,
    });
    canvasInitedRef.current = false;
  }, [image, setImageGeometry]);

  useEffect(() => {
    if (!imageGeometry || canvasInitedRef.current) return;
    canvasInitedRef.current = true;
    initCanvasView();
  }, [imageGeometry, initCanvasView]);

  const pointerToNatural = useCallback(
    (evt: { offsetX: number; offsetY: number }) => {
      if (!imageGeometry) return null;
      const display = containerToDisplay(evt.offsetX, evt.offsetY, transform);
      return displayToNaturalClamped(display, imageGeometry);
    },
    [imageGeometry, transform]
  );

  const handleStageClick = (evt: KonvaEventObject<MouseEvent>) => {
    if (mode === 'preview' && evt.target === evt.target.getStage()) {
      setSelectedRegionIndex(null);
      return;
    }
    if (mode !== 'calibrating' || !wrapRef.current || pendingPoint || panActive) return;
    const stage = evt.target.getStage();
    if (!stage || evt.target !== stage) return;
    const wrapRect = wrapRef.current.getBoundingClientRect();
    const screen = {
      x: evt.evt.clientX - wrapRect.left,
      y: evt.evt.clientY - wrapRect.top,
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
  const regionEditable = mode === 'preview' && !panActive;

  const onDragMove = (e: KonvaEventObject<DragEvent>) => {
    if (!panActive) return;
    const pos = clampPos({ x: e.target.x(), y: e.target.y() }, canvasScale, w, h);
    e.target.position(pos);
  };

  const onDragEnd = (e: KonvaEventObject<DragEvent>) => {
    if (!panActive) return;
    setCanvasStagePos(clampPos({ x: e.target.x(), y: e.target.y() }, canvasScale, w, h));
  };

  return (
    <div className="canvas-viewport">
      <CanvasToolbar
        contentWidth={w}
        contentHeight={h}
        regionEditable={mode === 'preview'}
      />
      <div
        ref={wrapRef}
        className="canvas-stage-viewport"
        onMouseMove={(e) => {
          if (mode !== 'calibrating' || !wrapRef.current || !imageGeometry) return;
          const rect = wrapRef.current.getBoundingClientRect();
          const screen = { x: e.clientX - rect.left, y: e.clientY - rect.top };
          const natural = pointerToNatural({ offsetX: screen.x, offsetY: screen.y });
          setHoverScreen(screen);
          setHoverNatural(natural);
        }}
        onMouseLeave={() => {
          setHoverNatural(null);
          setHoverScreen(null);
        }}
      >
        <Stage
          ref={stageRef}
          width={canvasViewport.w}
          height={canvasViewport.h}
          scaleX={canvasScale}
          scaleY={canvasScale}
          x={canvasStagePos.x}
          y={canvasStagePos.y}
          onWheel={handleWheel}
          draggable={panActive}
          onDragMove={onDragMove}
          onDragEnd={onDragEnd}
          onClick={handleStageClick}
          style={{
            cursor: panActive
              ? 'grab'
              : mode === 'calibrating'
                ? 'crosshair'
                : regionEditable
                  ? 'default'
                  : 'grab',
          }}
        >
          <Layer listening={false}>
            <KonvaImage image={image} width={w} height={h} listening={false} />
          </Layer>
          {showOverlay && (
            <Layer>
              <RegionOverlay
                regions={regions!.regions}
                naturalWidth={natural.x}
                naturalHeight={natural.y}
                canvasWidth={w}
                canvasHeight={h}
                editable={regionEditable}
                selectedIndex={selectedRegionIndex}
                onSelect={setSelectedRegionIndex}
                onBBoxChange={updateRegion}
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
            onNaturalChange={(nat) => setPendingPoint((p) => (p ? { ...p, natural: nat } : p))}
            onConfirm={confirmPending}
            onCancel={() => setPendingPoint(null)}
          />
        )}
      </div>
    </div>
  );
};
