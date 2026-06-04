import React, { useEffect, useRef } from 'react';
import { Rect, Transformer } from 'react-konva';
import type Konva from 'konva';
import { bboxToCanvasRect, canvasRectToBbox } from '../../utils/regions';

export type RegionItem = {
  kind: string;
  bbox: { x0: number; y0: number; x1: number; y1: number; confidence?: number };
  source?: string | null;
};

const KIND_COLORS: Record<string, string> = {
  plot_area: 'rgba(0,180,80,0.15)',
  legend: 'rgba(255,80,0,0.25)',
  legend_marker: 'rgba(255,120,0,0.35)',
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
  legend_marker: '#ff8800',
  title: '#7850ff',
  legend_default: '#ff5500',
};

const ANCHORS = [
  'top-left',
  'top-center',
  'top-right',
  'middle-left',
  'middle-right',
  'bottom-left',
  'bottom-center',
  'bottom-right',
];

type Props = {
  regions: RegionItem[];
  naturalWidth: number;
  naturalHeight: number;
  canvasWidth: number;
  canvasHeight: number;
  editable?: boolean;
  selectedIndex?: number | null;
  onSelect?: (index: number | null) => void;
  onBBoxChange?: (
    index: number,
    bbox: { x0: number; y0: number; x1: number; y1: number }
  ) => void;
};

export const RegionOverlay: React.FC<Props> = ({
  regions,
  naturalWidth,
  naturalHeight,
  canvasWidth,
  canvasHeight,
  editable = false,
  selectedIndex = null,
  onSelect,
  onBBoxChange,
}) => {
  const trRef = useRef<Konva.Transformer>(null);
  const shapeRefs = useRef<(Konva.Rect | null)[]>([]);

  useEffect(() => {
    const tr = trRef.current;
    if (!tr || !editable) return;
    const node =
      selectedIndex != null && selectedIndex >= 0
        ? shapeRefs.current[selectedIndex]
        : null;
    if (node) {
      tr.nodes([node]);
      tr.getLayer()?.batchDraw();
    } else {
      tr.nodes([]);
      tr.getLayer()?.batchDraw();
    }
  }, [selectedIndex, editable, regions]);

  const commitRect = (index: number, node: Konva.Rect) => {
    if (!onBBoxChange) return;
    const bbox = canvasRectToBbox(
      {
        x: node.x(),
        y: node.y(),
        width: Math.max(1, node.width() * node.scaleX()),
        height: Math.max(1, node.height() * node.scaleY()),
      },
      naturalWidth,
      naturalHeight,
      canvasWidth,
      canvasHeight
    );
    node.width(node.width() * node.scaleX());
    node.height(node.height() * node.scaleY());
    node.scaleX(1);
    node.scaleY(1);
    onBBoxChange(index, bbox);
  };

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
        const stroke =
          selectedIndex === i ? '#1677ff' : KIND_STROKES[r.kind] || '#888';
        const sourceDash = r.source === 'cv' ? [2, 2] : r.source === 'fused' ? [6, 3] : [4, 4];
        return (
          <Rect
            key={`region-${i}`}
            ref={(el) => {
              shapeRefs.current[i] = el;
            }}
            x={x}
            y={y}
            width={w}
            height={h}
            fill={fill}
            stroke={stroke}
            strokeWidth={selectedIndex === i ? 2.5 : r.kind === 'legend' ? 2 : 1}
            dash={r.kind === 'plot_area' ? undefined : sourceDash}
            listening={editable}
            draggable={editable}
            onMouseDown={(e) => {
              if (!editable) return;
              e.cancelBubble = true;
            }}
            onDragStart={(e) => {
              if (!editable) return;
              e.cancelBubble = true;
            }}
            onClick={(e) => {
              if (!editable) return;
              e.cancelBubble = true;
              onSelect?.(i);
            }}
            onTap={(e) => {
              if (!editable) return;
              e.cancelBubble = true;
              onSelect?.(i);
            }}
            onDragEnd={(e) => {
              if (!editable) return;
              e.cancelBubble = true;
              commitRect(i, e.target as Konva.Rect);
            }}
            onTransformEnd={(e) => {
              if (!editable) return;
              e.cancelBubble = true;
              commitRect(i, e.target as Konva.Rect);
            }}
          />
        );
      })}
      {editable && (
        <Transformer
          ref={trRef}
          rotateEnabled={false}
          keepRatio={false}
          enabledAnchors={ANCHORS}
          boundBoxFunc={(oldBox, newBox) => {
            if (newBox.width < 8 || newBox.height < 8) return oldBox;
            return newBox;
          }}
        />
      )}
    </>
  );
};
