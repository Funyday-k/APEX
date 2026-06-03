import React from 'react';
import { Rect } from 'react-konva';
import { naturalToDisplay, type ImageGeometry } from '../../store/useStore';

export type RegionItem = {
  kind: string;
  bbox: { x0: number; y0: number; x1: number; y1: number };
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
  geometry: ImageGeometry;
};

export const RegionOverlay: React.FC<Props> = ({ regions, geometry }) => {
  return (
    <>
      {regions.map((r, i) => {
        const tl = naturalToDisplay({ x: r.bbox.x0, y: r.bbox.y0 }, geometry);
        const br = naturalToDisplay({ x: r.bbox.x1, y: r.bbox.y1 }, geometry);
        const w = br.x - tl.x;
        const h = br.y - tl.y;
        if (w <= 0 || h <= 0) return null;
        const fill = KIND_COLORS[r.kind] || 'rgba(128,128,128,0.1)';
        const stroke = KIND_STROKES[r.kind] || '#888';
        return (
          <Rect
            key={`${r.kind}-${i}`}
            x={tl.x}
            y={tl.y}
            width={w}
            height={h}
            fill={fill}
            stroke={stroke}
            strokeWidth={r.kind === 'legend' ? 2 : 1}
            dash={r.kind === 'plot_area' ? undefined : [4, 4]}
            listening={false}
          />
        );
      })}
    </>
  );
};
