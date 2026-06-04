import { useT } from '../../i18n/useT';
import { useStore } from '../../store/useStore';
import { clampStagePos, zoomAtPoint } from '../../utils/canvasCoords';
import { centerStagePos } from '../../utils/regionBBox';
import { IconFitWindow, IconPan, IconResetView, IconZoomIn, IconZoomOut } from './icons';

type Props = {
  contentWidth: number;
  contentHeight: number;
  regionEditable?: boolean;
};

const MIN_SCALE = 1;
const MAX_SCALE = 4;

export function CanvasToolbar({ contentWidth, contentHeight, regionEditable = false }: Props) {
  const {
    canvasScale,
    canvasStagePos,
    canvasViewport,
    canvasPanMode,
    setCanvasPanMode,
    setCanvasScale,
    setCanvasStagePos,
    resetCanvasView,
    fitCanvasToViewport,
  } = useStore();
  const { t } = useT();

  const content = { w: contentWidth, h: contentHeight };

  const clampPos = (pos: { x: number; y: number }, scale: number) =>
    clampStagePos(pos, scale, canvasViewport, content);

  const applyZoom = (factor: number, center?: { x: number; y: number }) => {
    const ptr = center ?? {
      x: canvasViewport.w / 2,
      y: canvasViewport.h / 2,
    };
    let { scale, pos } = zoomAtPoint(
      canvasScale,
      canvasStagePos,
      ptr,
      factor,
      MIN_SCALE,
      MAX_SCALE
    );
    if (factor < 1 && scale < MIN_SCALE) {
      scale = MIN_SCALE;
      pos = centerStagePos(scale, canvasViewport, content);
    }
    setCanvasScale(scale);
    setCanvasStagePos(clampPos(pos, scale));
  };

  const pct = Math.round(canvasScale * 100);

  return (
    <div className="canvas-toolbar" role="toolbar" aria-label={t('canvasToolbar')}>
      <button
        type="button"
        className="btn-icon"
        onClick={() => applyZoom(1.15)}
        title={t('zoomIn')}
        aria-label={t('zoomIn')}
      >
        <IconZoomIn />
      </button>
      <button
        type="button"
        className="btn-icon"
        onClick={() => applyZoom(1 / 1.15)}
        title={t('zoomOut')}
        aria-label={t('zoomOut')}
        disabled={canvasScale <= MIN_SCALE + 1e-6}
      >
        <IconZoomOut />
      </button>
      <button
        type="button"
        className={`btn-icon${canvasPanMode ? ' active' : ''}`}
        onClick={() => setCanvasPanMode(!canvasPanMode)}
        title={t('panTool')}
        aria-label={t('panTool')}
        aria-pressed={canvasPanMode}
      >
        <IconPan />
      </button>
      <button
        type="button"
        className="btn-icon"
        onClick={resetCanvasView}
        title={t('zoomReset')}
        aria-label={t('zoomReset')}
      >
        <IconResetView />
      </button>
      <button
        type="button"
        className="btn-icon"
        onClick={() => fitCanvasToViewport()}
        title={t('zoomFit')}
        aria-label={t('zoomFit')}
      >
        <IconFitWindow />
      </button>
      <span className="canvas-zoom-pct">{pct}%</span>
      {regionEditable && (
        <span className="canvas-toolbar-hint">{t('regionDragHint')}</span>
      )}
    </div>
  );
}
