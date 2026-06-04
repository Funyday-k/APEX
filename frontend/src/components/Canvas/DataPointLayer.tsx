import React from 'react';
import { Circle, Layer, Line } from 'react-konva';
import { recomputePoint } from '../../services/api';
import {
  displayToNatural,
  naturalToDisplay,
  type Pixel,
  useStore,
} from '../../store/useStore';

type DragNode = {
  x: () => number;
  y: () => number;
  position: (pos: Pixel) => void;
  getLayer: () => { batchDraw: () => void } | null;
};

export const DataPointLayer: React.FC = () => {
  const {
    series,
    chartType,
    calibration,
    imageGeometry,
    pixelDisplayMode,
    updatePoint,
    removePoint,
    setError,
    suggestedRemovals,
  } = useStore();

  const removalSet = new Set(
    suggestedRemovals.map((r) => `${r.series_idx}:${r.point_idx}`)
  );

  const handleDragEnd = async (
    seriesIdx: number,
    pointIdx: number,
    pos: Pixel,
    previous: Pixel,
    node: DragNode
  ) => {
    if (!calibration) return;
    const sourcePos = imageGeometry ? displayToNatural(pos, imageGeometry) : pos;
    try {
      const res = await recomputePoint({
        calibration,
        pixel_points: [
          { series_idx: seriesIdx, point_idx: pointIdx, px: sourcePos.x, py: sourcePos.y },
        ],
      });
      const pt = res.points[0];
      const displayPixel = imageGeometry
        ? naturalToDisplay({ x: pt.px, y: pt.py }, imageGeometry)
        : { x: pt.px, y: pt.py };
      updatePoint(seriesIdx, pointIdx, { x: pt.x, y: pt.y }, displayPixel);
    } catch (e) {
      node.position(previous);
      node.getLayer()?.batchDraw();
      setError((e as Error).message);
    }
  };

  const showConnectLines =
    chartType === 'line' || series.some((s) => s.representation === 'marker_line');

  return (
    <Layer>
      {series.map((s, si) => {
        const displayPts =
          pixelDisplayMode === 'detected' &&
          s.detected_pixel_points &&
          s.detected_pixel_points.length > 0
            ? s.detected_pixel_points
            : s.pixel_points;

        return (
          <React.Fragment key={si}>
            {showConnectLines &&
              displayPts.length > 1 &&
              s.representation !== 'markers' && (
              <Line
                points={[...displayPts]
                  .sort((a, b) => a.x - b.x)
                  .flatMap((p) => [p.x, p.y])}
                stroke={s.color_hex || '#000'}
                strokeWidth={1.5}
              />
            )}
            {displayPts.map((p, pi) => {
              const flagged = removalSet.has(`${si}:${pi}`);
              const err = s.errors?.[pi] as
                | { y_err_upper?: number; y_err_lower?: number }
                | undefined;
              const dataPt = s.points[pi];
              return (
              <React.Fragment key={pi}>
                {pixelDisplayMode === 'data' && s.has_error_bars && dataPt && calibration && err && (
                  <Line
                    points={[
                      p.x,
                      p.y - 12,
                      p.x,
                      p.y + 12,
                    ]}
                    stroke={s.color_hex || '#1677ff'}
                    strokeWidth={1}
                    listening={false}
                  />
                )}
              <Circle
                x={p.x}
                y={p.y}
                radius={pixelDisplayMode === 'detected' ? 3 : flagged ? 6 : 4}
                fill={
                  flagged
                    ? 'rgba(255,0,80,0.85)'
                    : pixelDisplayMode === 'detected'
                    ? 'rgba(255,140,0,0.9)'
                    : s.color_hex || '#1677ff'
                }
                stroke={flagged ? '#ff0050' : '#fff'}
                strokeWidth={flagged ? 2 : 1}
                draggable={pixelDisplayMode === 'data'}
                onDblClick={() => removePoint(si, pi)}
                onDragEnd={(e) => {
                  if (pixelDisplayMode !== 'data') return;
                  const node = e.target;
                  handleDragEnd(si, pi, { x: node.x(), y: node.y() }, p, node);
                }}
              />
              </React.Fragment>
            );
            })}
          </React.Fragment>
        );
      })}
    </Layer>
  );
};
