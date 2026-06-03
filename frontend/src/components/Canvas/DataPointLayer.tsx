import React from 'react';
import { Circle, Layer, Line } from 'react-konva';
import { recomputePoint } from '../../services/api';
import { useStore } from '../../store/useStore';

export const DataPointLayer: React.FC = () => {
  const { series, calibration, updatePoint } = useStore();

  const handleDragEnd = async (
    seriesIdx: number,
    pointIdx: number,
    pos: { x: number; y: number }
  ) => {
    if (!calibration) return;
    try {
      const res = await recomputePoint({
        calibration,
        pixel_points: [
          { series_idx: seriesIdx, point_idx: pointIdx, px: pos.x, py: pos.y },
        ],
      });
      const pt = res.points[0];
      updatePoint(seriesIdx, pointIdx, { x: pt.x, y: pt.y }, { x: pt.px, y: pt.py });
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <Layer>
      {series.map((s, si) => (
        <React.Fragment key={si}>
          {s.pixel_points.length > 1 && (
            <Line
              points={s.pixel_points.flatMap((p) => [p.x, p.y])}
              stroke={s.color_hex || '#000'}
              strokeWidth={1.5}
            />
          )}
          {s.pixel_points.map((p, pi) => (
            <Circle
              key={pi}
              x={p.x}
              y={p.y}
              radius={4}
              fill={s.color_hex || '#1677ff'}
              stroke="#fff"
              strokeWidth={1}
              draggable
              onDragEnd={(e) => {
                const node = e.target;
                handleDragEnd(si, pi, { x: node.x(), y: node.y() });
              }}
            />
          ))}
        </React.Fragment>
      ))}
    </Layer>
  );
};
