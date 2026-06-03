import React from 'react';
import { Circle, Layer, Text } from 'react-konva';
import { useStore } from '../../store/useStore';

export const CalibrationLayer: React.FC = () => {
  const { xRefs, yRefs } = useStore();

  return (
    <Layer listening={false}>
      {xRefs.map((r, i) => (
        <React.Fragment key={`x${i}`}>
          <Circle
            x={r.pixel.x}
            y={r.pixel.y}
            radius={6}
            fill="red"
          />
          <Text
            x={r.pixel.x + 8}
            y={r.pixel.y}
            text={`X=${r.data.x}`}
            fontSize={14}
            fill="red"
          />
        </React.Fragment>
      ))}
      {yRefs.map((r, i) => (
        <React.Fragment key={`y${i}`}>
          <Circle
            x={r.pixel.x}
            y={r.pixel.y}
            radius={6}
            fill="blue"
          />
          <Text
            x={r.pixel.x + 8}
            y={r.pixel.y}
            text={`Y=${r.data.y}`}
            fontSize={14}
            fill="blue"
          />
        </React.Fragment>
      ))}
    </Layer>
  );
};
