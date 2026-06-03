# 附录 C：前端五步向导与交互流程

> 分册说明：进阶模块 C。与 [core/01-framework.md](../core/01-framework.md) §13–14 衔接。

## C.1 交互流程总览

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ 1.上传  │ → │ 2.分析  │ → │ 3.标定  │ → │ 4.提取  │ → │ 5.校正  │
│         │   │自动识别 │   │四点确认 │   │CV+VLM   │   │导出     │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

## C.2 完整状态管理 `frontend/src/store/useStore.ts`（完整版）

```typescript
import { create } from 'zustand';

export type Pixel = { x: number; y: number };
export type CalibPoint = { pixel: Pixel; data: Pixel };

export type SeriesData = {
  name: string;
  color_hex: string;
  points: { x: number; y: number }[];
  pixelPoints: Pixel[];      // 用于画布渲染
  confidence: number;
  hasErrorBars?: boolean;
};

export type Step = 'upload' | 'analyze' | 'calibrate' | 'extract' | 'review';

type State = {
  // 流程
  step: Step;
  loading: boolean;
  loadingMsg: string;

  // 图像
  imageUrl: string | null;
  imageId: string | null;
  imageSize: { w: number; h: number } | null;

  // 分析结果
  chartType: string;
  suggestedTicks: any | null;
  semantics: any | null;

  // 标定
  xRefs: CalibPoint[];
  yRefs: CalibPoint[];
  xScale: 'linear' | 'log';
  yScale: 'linear' | 'log';
  calibAxis: 'x' | 'y';

  // 提取结果
  series: SeriesData[];
  fitCurves: any[];
  flags: string[];
  overallConfidence: number;

  // Actions
  setStep: (s: Step) => void;
  setLoading: (b: boolean, msg?: string) => void;
  setImage: (url: string, id: string, w: number, h: number) => void;
  setAnalysis: (chartType: string, ticks: any, semantics: any) => void;
  addCalibPoint: (p: CalibPoint) => void;
  setCalibAxis: (a: 'x' | 'y') => void;
  setScale: (axis: 'x' | 'y', scale: 'linear' | 'log') => void;
  clearCalib: () => void;
  setExtraction: (data: any) => void;
  updatePoint: (si: number, pi: number,
                data: { x: number; y: number }, pixel: Pixel) => void;
  reset: () => void;
};

export const useStore = create<State>((set, get) => ({
  step: 'upload',
  loading: false,
  loadingMsg: '',
  imageUrl: null,
  imageId: null,
  imageSize: null,
  chartType: 'line',
  suggestedTicks: null,
  semantics: null,
  xRefs: [],
  yRefs: [],
  xScale: 'linear',
  yScale: 'linear',
  calibAxis: 'x',
  series: [],
  fitCurves: [],
  flags: [],
  overallConfidence: 0,

  setStep: (step) => set({ step }),
  setLoading: (loading, loadingMsg = '') => set({ loading, loadingMsg }),

  setImage: (imageUrl, imageId, w, h) =>
    set({ imageUrl, imageId, imageSize: { w, h }, step: 'analyze' }),

  setAnalysis: (chartType, suggestedTicks, semantics) =>
    set({
      chartType,
      suggestedTicks,
      semantics,
      xScale: semantics?.x_scale === 'log' ? 'log' : 'linear',
      yScale: semantics?.y_scale === 'log' ? 'linear' : 'linear',
      step: 'calibrate',
    }),

  addCalibPoint: (p) => {
    const { calibAxis, xRefs, yRefs } = get();
    if (calibAxis === 'x') {
      const next = [...xRefs, p].slice(-2);
      set({ xRefs: next, calibAxis: next.length >= 2 ? 'y' : 'x' });
    } else {
      set({ yRefs: [...yRefs, p].slice(-2) });
    }
  },

  setCalibAxis: (calibAxis) => set({ calibAxis }),
  setScale: (axis, scale) =>
    set(axis === 'x' ? { xScale: scale } : { yScale: scale }),
  clearCalib: () => set({ xRefs: [], yRefs: [], calibAxis: 'x' }),

  setExtraction: (data) =>
    set({
      series: data.series.map((s: any) => ({
        ...s,
        pixelPoints: s.pixelPoints || [],
      })),
      fitCurves: data.fit_curves || [],
      flags: data.low_confidence_flags || [],
      overallConfidence: data.overall_confidence || 0,
      step: 'review',
    }),

  updatePoint: (si, pi, data, pixel) =>
    set((state) => {
      const series = [...state.series];
      series[si] = { ...series[si] };
      series[si].points = [...series[si].points];
      series[si].pixelPoints = [...series[si].pixelPoints];
      series[si].points[pi] = data;
      series[si].pixelPoints[pi] = pixel;
      return { series };
    }),

  reset: () =>
    set({
      step: 'upload', imageUrl: null, imageId: null, imageSize: null,
      chartType: 'line', suggestedTicks: null, semantics: null,
      xRefs: [], yRefs: [], xScale: 'linear', yScale: 'linear',
      calibAxis: 'x', series: [], fitCurves: [], flags: [],
      overallConfidence: 0,
    }),
}));
```

## C.3 主应用与步骤导航 `frontend/src/App.tsx`

```tsx
import React from 'react';
import { useStore } from './store/useStore';
import { StepIndicator } from './components/StepIndicator';
import { UploadPanel } from './components/steps/UploadPanel';
import { AnalyzePanel } from './components/steps/AnalyzePanel';
import { CalibratePanel } from './components/steps/CalibratePanel';
import { ExtractPanel } from './components/steps/ExtractPanel';
import { ReviewPanel } from './components/steps/ReviewPanel';
import { LoadingOverlay } from './components/LoadingOverlay';

export default function App() {
  const { step, loading } = useStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: '100vh' }}>
      <header style={{ padding: '12px 24px', borderBottom: '1px solid #eee',
                       display: 'flex', alignItems: 'center', gap: 24 }}>
        <h1 style={{ margin: 0, fontSize: 20 }}>
          SciPlot Extractor · 科研图表提取
        </h1>
        <StepIndicator current={step} />
      </header>

      <main style={{ flex: 1, overflow: 'hidden' }}>
        {step === 'upload' && <UploadPanel />}
        {step === 'analyze' && <AnalyzePanel />}
        {step === 'calibrate' && <CalibratePanel />}
        {step === 'extract' && <ExtractPanel />}
        {step === 'review' && <ReviewPanel />}
      </main>

      {loading && <LoadingOverlay />}
    </div>
  );
}
```

## C.4 步骤指示器 `frontend/src/components/StepIndicator.tsx`

```tsx
import React from 'react';
import { Step } from '../store/useStore';

const STEPS: { key: Step; label: string }[] = [
  { key: 'upload', label: '1 上传' },
  { key: 'analyze', label: '2 分析' },
  { key: 'calibrate', label: '3 标定' },
  { key: 'extract', label: '4 提取' },
  { key: 'review', label: '5 校正导出' },
];

export const StepIndicator: React.FC<{ current: Step }> = ({ current }) => {
  const idx = STEPS.findIndex((s) => s.key === current);
  return (
    <div style={{ display: 'flex', gap: 8 }}>
      {STEPS.map((s, i) => (
        <div
          key={s.key}
          style={{
            padding: '4px 12px',
            borderRadius: 16,
            fontSize: 13,
            background: i === idx ? '#1677ff'
                       : i < idx ? '#e6f4ff' : '#f0f0f0',
            color: i === idx ? '#fff' : i < idx ? '#1677ff' : '#999',
          }}
        >
          {s.label}
        </div>
      ))}
    </div>
  );
};
```

## C.5 步骤一：上传 `frontend/src/components/steps/UploadPanel.tsx`

```tsx
import React, { useCallback } from 'react';
import { useStore } from '../../store/useStore';
import { uploadImage } from '../../services/api';

export const UploadPanel: React.FC = () => {
  const { setImage, setLoading } = useStore();

  const handleFile = useCallback(async (file: File) => {
    setLoading(true, '上传中...');
    try {
      const res = await uploadImage(file);
      // 读取图像尺寸
      const img = new Image();
      img.onload = () => {
        setImage(
          `http://localhost:8000${res.url}`,
          res.image_id,
          img.naturalWidth,
          img.naturalHeight
        );
        setLoading(false);
      };
      img.src = URL.createObjectURL(file);
    } catch (e) {
      alert('上传失败');
      setLoading(false);
    }
  }, [setImage, setLoading]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      style={{
        height: '100%', display: 'flex', alignItems: 'center',
        justifyContent: 'center', flexDirection: 'column',
      }}
    >
      <div
        style={{
          border: '2px dashed #1677ff', borderRadius: 12,
          padding: 60, textAlign: 'center', cursor: 'pointer',
          background: '#fafcff',
        }}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
        <p style={{ fontSize: 16, color: '#333' }}>
          点击或拖拽科研图表到此处
        </p>
        <p style={{ fontSize: 13, color: '#999' }}>
          支持 PNG / JPG / TIFF / WebP
        </p>
        <input
          id="file-input"
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
      </div>
    </div>
  );
};
```

## C.6 步骤二：自动分析 `frontend/src/components/steps/AnalyzePanel.tsx`

```tsx
import React, { useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { autoAnalyze } from '../../services/api';

export const AnalyzePanel: React.FC = () => {
  const {
    imageId, imageUrl, setAnalysis, setLoading,
    chartType, semantics, setStep,
  } = useStore();

  // 进入即自动触发分析
  useEffect(() => {
    if (!imageId) return;
    (async () => {
      setLoading(true, 'AI 正在分析图表类型与结构...');
      try {
        const res = await autoAnalyze(imageId);
        setAnalysis(res.chart_type, res.suggested_calibration,
                    res.semantics);
      } catch (e) {
        alert('分析失败');
      } finally {
        setLoading(false);
      }
    })();
  }, [imageId]);

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ flex: 1, padding: 24 }}>
        <img src={imageUrl!} alt=""
             style={{ maxWidth: '100%', maxHeight: '90%',
                      objectFit: 'contain' }} />
      </div>
      <aside style={{ width: 360, padding: 24, borderLeft: '1px solid #eee',
                      overflow: 'auto' }}>
        <h3>分析结果</h3>
        <Field label="图表类型" value={chartType} />
        <Field label="标题" value={semantics?.title} />
        <Field label="X 轴" value={semantics?.x_label} />
        <Field label="Y 轴" value={semantics?.y_label} />
        <Field label="X 刻度类型" value={semantics?.x_scale} />
        <Field label="Y 刻度类型" value={semantics?.y_scale} />
        <Field label="图例"
               value={(semantics?.legend || []).join(', ')} />

        <button
          style={btnStyle}
          onClick={() => setStep('calibrate')}
        >
          确认，进入坐标标定 →
        </button>
      </aside>
    </div>
  );
};

const Field: React.FC<{ label: string; value: any }> = ({ label, value }) => (
  <div style={{ marginBottom: 12 }}>
    <div style={{ fontSize: 12, color: '#999' }}>{label}</div>
    <div style={{ fontSize: 14 }}>{value || '—'}</div>
  </div>
);

const btnStyle: React.CSSProperties = {
  marginTop: 24, width: '100%', padding: '10px',
  background: '#1677ff', color: '#fff', border: 'none',
  borderRadius: 6, cursor: 'pointer', fontSize: 14,
};
```

## C.7 步骤三：标定面板（核心交互）`frontend/src/components/steps/CalibratePanel.tsx`

```tsx
import React, { useRef, useState } from 'react';
import { Stage, Layer, Image as KImage, Circle, Text, Line } from 'react-konva';
import useImage from 'use-image';
import { useStore } from '../../store/useStore';

export const CalibratePanel: React.FC = () => {
  const {
    imageUrl, xRefs, yRefs, calibAxis, addCalibPoint,
    setCalibAxis, clearCalib, xScale, yScale, setScale, setStep,
  } = useStore();
  const [image] = useImage(imageUrl || '');
  const [scale, setStageScale] = useState(1);
  const stageRef = useRef<any>(null);

  const canExtract = xRefs.length === 2 && yRefs.length === 2;

  const handleClick = (e: any) => {
    const stage = e.target.getStage();
    const pos = stage.getRelativePointerPosition();
    const axisLabel = calibAxis.toUpperCase();
    const input = prompt(
      `请输入此点在 ${axisLabel} 轴上的真实数据值：`
    );
    if (input === null || input.trim() === '') return;
    const val = parseFloat(input);
    if (isNaN(val)) {
      alert('请输入有效数字');
      return;
    }
    addCalibPoint({
      pixel: { x: pos.x, y: pos.y },
      data: calibAxis === 'x' ? { x: val, y: 0 } : { x: 0, y: val },
    });
  };

  const handleWheel = (e: any) => {
    e.evt.preventDefault();
    const oldScale = stageRef.current.scaleX();
    const newScale = e.evt.deltaY > 0 ? oldScale / 1.1 : oldScale * 1.1;
    setStageScale(Math.max(0.2, Math.min(5, newScale)));
  };

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      {/* 画布 */}
      <div style={{ flex: 1, background: '#f5f5f5' }}>
        <Stage
          ref={stageRef}
          width={window.innerWidth - 340}
          height={window.innerHeight - 120}
          scaleX={scale}
          scaleY={scale}
          draggable
          onWheel={handleWheel}
          onClick={handleClick}
        >
          <Layer>
            {image && <KImage image={image} />}
          </Layer>
          <Layer>
            {/* X 标定点 - 红 */}
            {xRefs.map((r, i) => (
              <CalibMarker key={`x${i}`} r={r} color="#e63946"
                           label={`X=${r.data.x}`} />
            ))}
            {/* Y 标定点 - 蓝 */}
            {yRefs.map((r, i) => (
              <CalibMarker key={`y${i}`} r={r} color="#1d3557"
                           label={`Y=${r.data.y}`} />
            ))}
            {/* 辅助连线 */}
            {xRefs.length === 2 && (
              <Line points={[xRefs[0].pixel.x, xRefs[0].pixel.y,
                             xRefs[1].pixel.x, xRefs[1].pixel.y]}
                    stroke="#e63946" strokeWidth={1} dash={[4, 4]} />
            )}
            {yRefs.length === 2 && (
              <Line points={[yRefs[0].pixel.x, yRefs[0].pixel.y,
                             yRefs[1].pixel.x, yRefs[1].pixel.y]}
                    stroke="#1d3557" strokeWidth={1} dash={[4, 4]} />
            )}
          </Layer>
        </Stage>
      </div>

      {/* 控制面板 */}
      <aside style={{ width: 340, padding: 24, borderLeft: '1px solid #eee',
                      overflow: 'auto' }}>
        <h3>坐标系标定</h3>
        <p style={{ fontSize: 13, color: '#666' }}>
          请在图上点击坐标轴上 <b>已知数值</b> 的位置，
          各轴需 2 个参考点。
        </p>

        {/* 当前标定轴 */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 12, color: '#999' }}>
            当前标定轴
          </label>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <AxisBtn active={calibAxis === 'x'}
                     onClick={() => setCalibAxis('x')}
                     label={`X 轴 (${xRefs.length}/2)`} color="#e63946" />
            <AxisBtn active={calibAxis === 'y'}
                     onClick={() => setCalibAxis('y')}
                     label={`Y 轴 (${yRefs.length}/2)`} color="#1d3557" />
          </div>
        </div>

        {/* 刻度类型 */}
        <div style={{ marginBottom: 16 }}>
          <ScaleSelect label="X 轴类型" value={xScale}
                       onChange={(v) => setScale('x', v)} />
          <ScaleSelect label="Y 轴类型" value={yScale}
                       onChange={(v) => setScale('y', v)} />
        </div>

        <button onClick={clearCalib} style={ghostBtn}>
          清除所有标定点
        </button>

        <button
          disabled={!canExtract}
          onClick={() => setStep('extract')}
          style={{ ...primaryBtn,
                   opacity: canExtract ? 1 : 0.4,
                   cursor: canExtract ? 'pointer' : 'not-allowed' }}
        >
          {canExtract ? '开始提取数据 →' : '请完成 4 个标定点'}
        </button>
      </aside>
    </div>
  );
};

const CalibMarker: React.FC<{ r: any; color: string; label: string }> =
  ({ r, color, label }) => (
  <>
    <Circle x={r.pixel.x} y={r.pixel.y} radius={5} fill={color}
            stroke="#fff" strokeWidth={1.5} />
    <Text x={r.pixel.x + 8} y={r.pixel.y - 6} text={label}
          fontSize={13} fill={color} />
  </>
);

const AxisBtn: React.FC<any> = ({ active, onClick, label, color }) => (
  <button onClick={onClick}
    style={{ flex: 1, padding: '6px', borderRadius: 6, fontSize: 13,
             border: `1px solid ${color}`,
             background: active ? color : '#fff',
             color: active ? '#fff' : color, cursor: 'pointer' }}>
    {label}
  </button>
);

const ScaleSelect: React.FC<any> = ({ label, value, onChange }) => (
  <div style={{ marginBottom: 8 }}>
    <label style={{ fontSize: 12, color: '#999' }}>{label}</label>
    <select value={value} onChange={(e) => onChange(e.target.value)}
            style={{ width: '100%', padding: 6, marginTop: 2 }}>
      <option value="linear">线性 (linear)</option>
      <option value="log">对数 (log)</option>
    </select>
  </div>
);

const primaryBtn: React.CSSProperties = {
  marginTop: 24, width: '100%', padding: 10, background: '#1677ff',
  color: '#fff', border: 'none', borderRadius: 6, fontSize: 14,
};
const ghostBtn: React.CSSProperties = {
  width: '100%', padding: 8, background: '#fff', color: '#666',
  border: '1px solid #ddd', borderRadius: 6, cursor: 'pointer',
  fontSize: 13, marginTop: 8,
};
```

## C.8 步骤四：执行提取 `frontend/src/components/steps/ExtractPanel.tsx`

```tsx
import React, { useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { extractData } from '../../services/api';

export const ExtractPanel: React.FC = () => {
  const {
    imageId, chartType, xRefs, yRefs, xScale, yScale,
    setExtraction, setLoading,
  } = useStore();

  useEffect(() => {
    (async () => {
      setLoading(true, 'CV 引擎正在提取数据点...');
      try {
        // 构造标定配置
        const calibration = {
          x_axis: {
            scale: xScale,
            ref1: { pixel: xRefs[0].pixel, data: xRefs[0].data },
            ref2: { pixel: xRefs[1].pixel, data: xRefs[1].data },
          },
          y_axis: {
            scale: yScale,
            ref1: { pixel: yRefs[0].pixel, data: yRefs[0].data },
            ref2: { pixel: yRefs[1].pixel, data: yRefs[1].data },
          },
        };

        const result = await extractData({
          image_id: imageId,
          chart_type: chartType,
          calibration,
        });
        setExtraction(result);
      } catch (e) {
        alert('提取失败');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div style={{ display: 'flex', alignItems: 'center',
                  justifyContent: 'center', height: '100%' }}>
      <p style={{ color: '#666' }}>正在提取，请稍候...</p>
    </div>
  );
};
```

## C.9 步骤五：校正与导出（核心）`frontend/src/components/steps/ReviewPanel.tsx`

```tsx
import React from 'react';
import { ReviewCanvas } from '../review/ReviewCanvas';
import { RebuiltChart } from '../review/RebuiltChart';
import { ExportBar } from '../review/ExportBar';
import { useStore } from '../../store/useStore';

export const ReviewPanel: React.FC = () => {
  const { flags, overallConfidence } = useStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: '100%' }}>
      {/* 置信度 + 警告条 */}
      <div style={{ padding: '8px 24px', background: '#fffbe6',
                    borderBottom: '1px solid #ffe58f',
                    display: flags.length ? 'block' : 'none' }}>
        <b>整体置信度：{(overallConfidence * 100).toFixed(1)}%</b>
        {flags.map((f, i) => (
          <div key={i} style={{ fontSize: 13, color: '#ad6800' }}>
            ⚠ {f}
          </div>
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左：原图叠加可拖拽数据点 */}
        <div style={{ flex: 1, borderRight: '1px solid #eee' }}>
          <div style={{ padding: 8, fontSize: 13, color: '#999' }}>
            原图 · 拖拽红点可校正，双击空白处增点
          </div>
          <ReviewCanvas />
        </div>

        {/* 右：重建图对比 */}
        <div style={{ flex: 1 }}>
          <div style={{ padding: 8, fontSize: 13, color: '#999' }}>
            重建图 · 实时验证提取正确性
          </div>
          <RebuiltChart />
        </div>
      </div>

      <ExportBar />
    </div>
  );
};
```

## C.10 校正画布（拖拽重算）`frontend/src/components/review/ReviewCanvas.tsx`

```tsx
import React, { useRef, useState } from 'react';
import { Stage, Layer, Image as KImage, Circle, Line } from 'react-konva';
import useImage from 'use-image';
import { useStore } from '../../store/useStore';
import { recomputePoint } from '../../services/api';

export const ReviewCanvas: React.FC = () => {
  const {
    imageUrl, series, updatePoint, xRefs, yRefs, xScale, yScale,
  } = useStore();
  const [image] = useImage(imageUrl || '');
  const [scale, setScale] = useState(1);
  const stageRef = useRef<any>(null);

  const buildCalibration = () => ({
    x_axis: {
      scale: xScale,
      ref1: { pixel: xRefs[0].pixel, data: xRefs[0].data },
      ref2: { pixel: xRefs[1].pixel, data: xRefs[1].data },
    },
    y_axis: {
      scale: yScale,
      ref1: { pixel: yRefs[0].pixel, data: yRefs[0].data },
      ref2: { pixel: yRefs[1].pixel, data: yRefs[1].data },
    },
  });

  // 拖拽结束 → 调用后端重算数据坐标
  const handleDragEnd = async (si: number, pi: number, e: any) => {
    const pos = e.target.position();
    const res = await recomputePoint({
      calibration: buildCalibration(),
      pixel_points: [{ series_idx: si, point_idx: pi,
                       px: pos.x, py: pos.y }],
    });
    const np = res.points[0];
    updatePoint(si, pi, { x: np.x, y: np.y },
                { x: pos.x, y: pos.y });
  };

  const handleWheel = (e: any) => {
    e.evt.preventDefault();
    const old = stageRef.current.scaleX();
    setScale(Math.max(0.2, Math.min(5,
      e.evt.deltaY > 0 ? old / 1.1 : old * 1.1)));
  };

  return (
    <Stage
      ref={stageRef}
      width={window.innerWidth / 2 - 20}
      height={window.innerHeight - 200}
      scaleX={scale}
      scaleY={scale}
      draggable
      onWheel={handleWheel}
    >
      <Layer>
        {image && <KImage image={image} />}
      </Layer>
      <Layer>
        {series.map((s, si) => (
          <React.Fragment key={si}>
            {/* 折线连接（仅折线图）*/}
            <Line
              points={s.pixelPoints.flatMap((p) => [p.x, p.y])}
              stroke={s.color_hex}
              strokeWidth={1}
              opacity={0.5}
            />
            {/* 可拖拽数据点 */}
            {s.pixelPoints.map((p, pi) => (
              <Circle
                key={pi}
                x={p.x}
                y={p.y}
                radius={4}
                fill={s.color_hex}
                stroke="#fff"
                strokeWidth={1}
                draggable
                onDragEnd={(e) => handleDragEnd(si, pi, e)}
                onMouseEnter={(e) => {
                  e.target.getStage()!.container().style.cursor = 'move';
                  e.target.radius(6);
                }}
                onMouseLeave={(e) => {
                  e.target.getStage()!.container().style.cursor = 'default';
                  e.target.radius(4);
                }}
              />
            ))}
          </React.Fragment>
        ))}
      </Layer>
    </Stage>
  );
};
```

## C.11 重建图 `frontend/src/components/review/RebuiltChart.tsx`

```tsx
import React from 'react';
import ReactECharts from 'echarts-for-react';
import { useStore } from '../../store/useStore';

export const RebuiltChart: React.FC = () => {
  const { series, fitCurves, chartType, semantics } = useStore();

  const seriesConfig = [
    ...series.map((s) => ({
      name: s.name,
      type: chartType === 'scatter' ? 'scatter' : 'line',
      symbolSize: chartType === 'scatter' ? 8 : 4,
      data: s.points.map((p) => [p.x, p.y]),
      itemStyle: { color: s.color_hex },
      lineStyle: { color: s.color_hex },
    })),
    // 拟合曲线用虚线表示
    ...fitCurves.map((f: any) => ({
      name: f.name + ` (${f.curve_type})`,
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: f.points.map((p: any) => [p.x, p.y]),
      lineStyle: { color: f.color_hex, type: 'dashed', width: 2 },
    })),
  ];

  const option = {
    tooltip: { trigger: 'item',
               formatter: (p: any) =>
                 `${p.seriesName}<br/>x: ${p.value[0].toFixed(3)}<br/>` +
                 `y: ${p.value[1].toFixed(3)}` },
    legend: { type: 'scroll', top: 0 },
    grid: { top: 40, left: 50, right: 20, bottom: 40 },
    xAxis: {
      type: semantics?.x_scale === 'log' ? 'log' : 'value',
      name: semantics?.x_label || 'X',
      nameLocation: 'middle', nameGap: 25,
    },
    yAxis: {
      type: semantics?.y_scale === 'log' ? 'log' : 'value',
      name: semantics?.y_label || 'Y',
      nameLocation: 'middle', nameGap: 35,
    },
    series: seriesConfig,
  };

  return <ReactECharts option={option}
                       style={{ height: 'calc(100% - 30px)' }}
                       notMerge />;
};
```

## C.12 导出栏 `frontend/src/components/review/ExportBar.tsx`

```tsx
import React from 'react';
import { useStore } from '../../store/useStore';
import { exportResult } from '../../services/api';

export const ExportBar: React.FC = () => {
  const { imageId, series, reset } = useStore();

  const totalPoints = series.reduce((sum, s) => sum + s.points.length, 0);

  const handleExport = async (fmt: 'csv' | 'excel' | 'json' | 'pdf') => {
    const blob = await exportResult(imageId!, fmt, series);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const ext = { csv: 'csv', excel: 'xlsx', json: 'json', pdf: 'pdf' }[fmt];
    a.download = `extracted_data.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ padding: '12px 24px', borderTop: '1px solid #eee',
                  display: 'flex', alignItems: 'center', gap: 12 }}>
      <span style={{ color: '#666', fontSize: 13 }}>
        共 {series.length} 个系列 · {totalPoints} 个数据点
      </span>
      <div style={{ flex: 1 }} />
      <button onClick={() => handleExport('csv')} style={btn}>
        导出 CSV
      </button>
      <button onClick={() => handleExport('excel')} style={btn}>
        导出 Excel
      </button>
      <button onClick={() => handleExport('json')} style={btn}>
        导出 JSON
      </button>
      <button onClick={() => handleExport('pdf')} style={btn}>
        导出 PDF 报告
      </button>
      <button onClick={reset}
              style={{ ...btn, background: '#fff', color: '#666',
                       border: '1px solid #ddd' }}>
        处理新图
      </button>
    </div>
  );
};

const btn: React.CSSProperties = {
  padding: '8px 16px', background: '#1677ff', color: '#fff',
  border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13,
};
```

## C.13 API 服务补全 `frontend/src/services/api.ts`（完整版）

```typescript
const BASE = 'http://localhost:8000/api';

export async function uploadImage(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/projects/upload`, {
    method: 'POST', body: form,
  });
  if (!res.ok) throw new Error('upload failed');
  return res.json();
}

export async function autoAnalyze(imageId: string) {
  const res = await fetch(`${BASE}/extract/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId }),
  });
  if (!res.ok) throw new Error('analyze failed');
  return res.json();
}

export async function extractData(payload: any) {
  const res = await fetch(`${BASE}/extract/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('extract failed');
  return res.json();
}

export async function recomputePoint(payload: any) {
  const res = await fetch(`${BASE}/calibrate/recompute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function exportResult(
  imageId: string,
  format: 'csv' | 'excel' | 'json' | 'pdf',
  series: any[]
) {
  const res = await fetch(`${BASE}/export/${imageId}?format=${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ series }),  // 传入校正后的最新数据
  });
  return res.blob();
}
```

## C.14 加载遮罩 `frontend/src/components/LoadingOverlay.tsx`

```tsx
import React from 'react';
import { useStore } from '../store/useStore';

export const LoadingOverlay: React.FC = () => {
  const { loadingMsg } = useStore();
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{ background: '#fff', padding: '24px 40px',
                    borderRadius: 8, textAlign: 'center' }}>
        <div className="spinner" style={{
          width: 32, height: 32, border: '3px solid #eee',
          borderTopColor: '#1677ff', borderRadius: '50%',
          margin: '0 auto 12px', animation: 'spin 0.8s linear infinite',
        }} />
        <div style={{ color: '#666' }}>{loadingMsg || '处理中...'}</div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};
```

## C.15 前端依赖 `frontend/package.json`

```json
{
  "name": "sciplot-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.5.0",
    "konva": "^9.3.0",
    "react-konva": "^18.2.10",
    "use-image": "^1.1.1",
    "echarts": "^5.5.0",
    "echarts-for-react": "^3.0.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.1.0"
  }
}
```

---

