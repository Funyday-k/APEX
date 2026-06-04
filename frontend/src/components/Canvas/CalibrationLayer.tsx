import React from 'react';
import { Circle, Layer, Text } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import { naturalToDisplayClamped, displayToNaturalClamped } from '../../utils/canvasCoords';
import { useStore, type ImageGeometry } from '../../store/useStore';

type PendingPoint = {
  axis: 'x' | 'y';
  natural: { x: number; y: number };
};

type Props = {
  pendingPoint?: PendingPoint | null;
  interactive?: boolean;
  geometry: ImageGeometry;
  onSelectRef?: (axis: 'x' | 'y', index: number) => void;
  onDragRef?: (axis: 'x' | 'y', index: number, natural: { x: number; y: number }) => void;
};

export const CalibrationLayer: React.FC<Props> = ({
  pendingPoint,
  interactive = false,
  geometry,
  onSelectRef,
  onDragRef,
}) => {
  const { xRefs, yRefs, selectedCalib } = useStore();

  const toDisplay = (natural: { x: number; y: number }) =>
    naturalToDisplayClamped(natural, geometry);

  const handleDragEnd =
    (axis: 'x' | 'y', index: number) => (e: KonvaEventObject<DragEvent>) => {
      const node = e.target;
      const natural = displayToNaturalClamped({ x: node.x(), y: node.y() }, geometry);
      onDragRef?.(axis, index, natural);
    };

  return (
    <Layer listening={interactive}>
      {xRefs.map((r, i) => {
        const d = toDisplay(r.pixel);
        const selected = selectedCalib?.axis === 'x' && selectedCalib.index === i;
        return (
          <React.Fragment key={`x${i}`}>
            <Circle
              x={d.x}
              y={d.y}
              radius={selected ? 8 : 6}
              fill={selected ? '#ff5252' : 'red'}
              stroke="#fff"
              strokeWidth={selected ? 2 : 1}
              draggable={interactive}
              onClick={(e) => {
                e.cancelBubble = true;
                onSelectRef?.('x', i);
              }}
              onTap={(e) => {
                e.cancelBubble = true;
                onSelectRef?.('x', i);
              }}
              onDragEnd={handleDragEnd('x', i)}
            />
            <Text
              x={d.x + 8}
              y={d.y}
              text={`X=${r.data.x}`}
              fontSize={14}
              fill="red"
              listening={false}
            />
          </React.Fragment>
        );
      })}
      {yRefs.map((r, i) => {
        const d = toDisplay(r.pixel);
        const selected = selectedCalib?.axis === 'y' && selectedCalib.index === i;
        return (
          <React.Fragment key={`y${i}`}>
            <Circle
              x={d.x}
              y={d.y}
              radius={selected ? 8 : 6}
              fill={selected ? '#42a5f5' : 'blue'}
              stroke="#fff"
              strokeWidth={selected ? 2 : 1}
              draggable={interactive}
              onClick={(e) => {
                e.cancelBubble = true;
                onSelectRef?.('y', i);
              }}
              onTap={(e) => {
                e.cancelBubble = true;
                onSelectRef?.('y', i);
              }}
              onDragEnd={handleDragEnd('y', i)}
            />
            <Text
              x={d.x + 8}
              y={d.y}
              text={`Y=${r.data.y}`}
              fontSize={14}
              fill="blue"
              listening={false}
            />
          </React.Fragment>
        );
      })}
      {pendingPoint && (
        <Circle
          x={toDisplay(pendingPoint.natural).x}
          y={toDisplay(pendingPoint.natural).y}
          radius={8}
          stroke={pendingPoint.axis === 'x' ? 'red' : 'blue'}
          strokeWidth={2}
          fill="rgba(255,255,255,0.4)"
          dash={[4, 4]}
          listening={false}
        />
      )}
    </Layer>
  );
};
