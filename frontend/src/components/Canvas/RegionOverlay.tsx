import React from 'react';
import { Rect } from 'react-konva';
import { bboxToCanvasRect } from '../../utils/regions';

export type RegionItem = {
  kind: string;
  bbox: { x0: number; y0: number; x1: number; y1: number; confidence?: number };
  source?: string | null;
};

const KIND_COLORS: Record<string, string> = {
  plot_area: 'rgba(0,180,80,0.15)',
  legend: 'rgba(255,80,0,0.25)',
  title: 'rgba(120,80,255,0.2)',
  x_axis: 'rgba(100,100,100,0.15)',
  y_axis: 'rgba(100,100,100,0.15)',
  x_tick_labels: 'rgba(80,80,200,0.12)',
  y_tick_labels: 'rgba(80,80,200,0.12)',
  colorbar: 'rgba(200,100,0,0.15)',
  other_text: 'rgba(150,150,150,0.12)',
};

const KIND_STROKES: Record<string, string> = {
  plot_area: '#00b450',
  legend: '#ff5500',
  title: '#7850ff',
  legend_default: '#ff5500',
};

type Props = {
  regions: RegionItem[];
  naturalWidth: number;
  naturalHeight: number;
  canvasWidth: number;
  canvasHeight: number;
};

export const RegionOverlay: React.FC<Props> = ({
  regions,
  naturalWidth,
  naturalHeight,
  canvasWidth,
  canvasHeight,
}) => {
  return (
    <>
      {regions.map((r, i) => {
        const rect = bboxToCanvasRect(
          r.bbox,
          naturalWidth,
          naturalHeight,
          canvasWidth,
          canvasHeight
        );
        const { x, y, width: w, height: h } = rect;
        if (w <= 0 || h <= 0) return null;
        const fill = KIND_COLORS[r.kind] || 'rgba(128,128,128,0.1)';
        const stroke = KIND_STROKES[r.kind] || '#888';
        const sourceDash = r.source === 'cv' ? [2, 2] : r.source === 'fused' ? [6, 3] : [4, 4];
        return (
          <Rect
            key={`${r.kind}-${i}`}
            x={x}
            y={y}
            width={w}
            height={h}
            fill={fill}
            stroke={stroke}
            strokeWidth={r.kind === 'legend' ? 2 : 1}
            dash={r.kind === 'plot_area' ? undefined : sourceDash}
            listening={false}
          />
        );
      })}
    </>
  );
};
