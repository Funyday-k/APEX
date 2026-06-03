import React from 'react';
import { Circle, Layer, Text } from 'react-konva';
import { useT } from '../../i18n/useT';
import { useStore } from '../../store/useStore';

export const CalibrationLayer: React.FC = () => {
  const { xRefs, yRefs, calibAxis, addCalibPoint } = useStore();
  const { t } = useT();

  const handleClick = (e: { target: { getStage: () => unknown } }) => {
    const stage = e.target.getStage() as {
      getRelativePointerPosition: () => { x: number; y: number } | null;
    } | null;
    if (!stage) return;
    const pos = stage.getRelativePointerPosition();
    if (!pos) return;

    const value = prompt(t('calibPrompt', { axis: calibAxis.toUpperCase() }));
    if (value === null || value.trim() === '') return;
    const num = parseFloat(value);
    if (Number.isNaN(num)) return;

    addCalibPoint({
      pixel: { x: pos.x, y: pos.y },
      data: calibAxis === 'x' ? { x: num, y: 0 } : { x: 0, y: num },
    });
  };

  return (
    <Layer onClick={handleClick}>
      {xRefs.map((r, i) => (
        <React.Fragment key={`x${i}`}>
          <Circle x={r.pixel.x} y={r.pixel.y} radius={6} fill="red" />
          <Text x={r.pixel.x + 8} y={r.pixel.y} text={`X=${r.data.x}`} fontSize={14} fill="red" />
        </React.Fragment>
      ))}
      {yRefs.map((r, i) => (
        <React.Fragment key={`y${i}`}>
          <Circle x={r.pixel.x} y={r.pixel.y} radius={6} fill="blue" />
          <Text x={r.pixel.x + 8} y={r.pixel.y} text={`Y=${r.data.y}`} fontSize={14} fill="blue" />
        </React.Fragment>
      ))}
    </Layer>
  );
};
