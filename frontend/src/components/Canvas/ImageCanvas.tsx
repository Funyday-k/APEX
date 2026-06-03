import React, { useRef, useState } from 'react';
import { Image as KonvaImage, Layer, Stage } from 'react-konva';
import useImage from 'use-image';
import { useStore } from '../../store/useStore';
import { CalibrationLayer } from './CalibrationLayer';
import { DataPointLayer } from './DataPointLayer';

type Props = { mode: 'calibrating' | 'extracted' };

export const ImageCanvas: React.FC<Props> = ({ mode }) => {
  const { imageUrl } = useStore();
  const [image] = useImage(imageUrl || '', 'anonymous');
  const [scale, setScale] = useState(1);
  const stageRef = useRef(null);

  const handleWheel = (e: { evt: WheelEvent }) => {
    e.evt.preventDefault();
    setScale((s) => Math.min(4, Math.max(0.2, e.evt.deltaY > 0 ? s / 1.1 : s * 1.1)));
  };

  if (!imageUrl) return <div className="canvas-placeholder">请先上传图片</div>;
  if (!image) return <div className="canvas-placeholder">加载图片中…</div>;

  const w = Math.min(900, image.width);
  const h = Math.min(650, (image.height / image.width) * w);

  return (
    <Stage
      ref={stageRef}
      width={w}
      height={h}
      scaleX={scale}
      scaleY={scale}
      onWheel={handleWheel}
      draggable
    >
      <Layer>
        <KonvaImage image={image} width={w} height={h} />
      </Layer>
      {mode === 'calibrating' && <CalibrationLayer />}
      {mode === 'extracted' && <DataPointLayer />}
    </Stage>
  );
};
