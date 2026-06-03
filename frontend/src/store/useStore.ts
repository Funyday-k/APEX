import { create } from 'zustand';
import type { Locale } from '../i18n/translations';

function loadLocale(): Locale {
  try {
    const saved = localStorage.getItem('sciplot-locale');
    if (saved === 'en' || saved === 'zh') return saved;
  } catch {
    /* ignore */
  }
  return 'zh';
}

export type Pixel = { x: number; y: number };
export type CalibPoint = { pixel: Pixel; data: Pixel };
export type Step = 'upload' | 'analyze' | 'calibrate' | 'extract' | 'review';
export type ChartTypeId = 'line' | 'scatter' | 'bar' | 'heatmap' | 'box';

export type SeriesData = {
  name: string;
  color_hex?: string;
  points: { x: number; y: number }[];
  pixel_points: Pixel[];
  confidence?: number;
  has_error_bars?: boolean;
};

export type CalibrationConfigPayload = {
  x_axis: { scale: 'linear' | 'log'; ref1: CalibPoint; ref2: CalibPoint };
  y_axis: { scale: 'linear' | 'log'; ref1: CalibPoint; ref2: CalibPoint };
};

type State = {
  locale: Locale;
  step: Step;
  loading: boolean;
  loadingMsg: string;
  error: string | null;

  imageUrl: string | null;
  imageId: string | null;

  chartType: ChartTypeId;
  suggestedTicks: Record<string, unknown> | null;
  semantics: Record<string, unknown> | null;

  xRefs: CalibPoint[];
  yRefs: CalibPoint[];
  xScale: 'linear' | 'log';
  yScale: 'linear' | 'log';
  calibAxis: 'x' | 'y';

  heatmapOptions: {
    colorbar_box: { x0: number; y0: number; x1: number; y1: number };
    value_range: [number, number];
    grid: [number, number];
  } | null;

  series: SeriesData[];
  fitCurves: Array<Record<string, unknown>>;
  flags: string[];
  overallConfidence: number;
  calibration: CalibrationConfigPayload | null;

  setLocale: (locale: Locale) => void;
  setStep: (s: Step) => void;
  setLoading: (b: boolean, msg?: string) => void;
  setError: (msg: string | null) => void;
  setImage: (url: string, id: string) => void;
  setAnalysis: (chartType: string, ticks: unknown, semantics: unknown) => void;
  setChartType: (t: ChartTypeId) => void;
  addCalibPoint: (p: CalibPoint) => void;
  setCalibAxis: (a: 'x' | 'y') => void;
  setScale: (axis: 'x' | 'y', scale: 'linear' | 'log') => void;
  clearCalib: () => void;
  setHeatmapOptions: (o: State['heatmapOptions']) => void;
  setExtraction: (data: Record<string, unknown>, cal: CalibrationConfigPayload) => void;
  updatePoint: (si: number, pi: number, data: { x: number; y: number }, pixel: Pixel) => void;
  reset: () => void;
};

const initial = {
  locale: loadLocale(),
  step: 'upload' as Step,
  loading: false,
  loadingMsg: '',
  error: null,
  imageUrl: null,
  imageId: null,
  chartType: 'line' as ChartTypeId,
  suggestedTicks: null,
  semantics: null,
  xRefs: [] as CalibPoint[],
  yRefs: [] as CalibPoint[],
  xScale: 'linear' as const,
  yScale: 'linear' as const,
  calibAxis: 'x' as const,
  heatmapOptions: null,
  series: [] as SeriesData[],
  fitCurves: [] as Array<Record<string, unknown>>,
  flags: [] as string[],
  overallConfidence: 0,
  calibration: null,
};

export const useStore = create<State>((set, get) => ({
  ...initial,

  setLocale: (locale) => {
    try {
      localStorage.setItem('sciplot-locale', locale);
    } catch {
      /* ignore */
    }
    document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en';
    set({ locale });
  },
  setStep: (step) => set({ step }),
  setLoading: (loading, loadingMsg = '') => set({ loading, loadingMsg }),
  setError: (error) => set({ error }),
  setImage: (imageUrl, imageId) =>
    set({ imageUrl, imageId, step: 'analyze', error: null, xRefs: [], yRefs: [] }),
  setAnalysis: (chartType, suggestedTicks, semantics) => {
    const sem = semantics as Record<string, unknown> | null;
    set({
      chartType: normalizeChartType(chartType),
      suggestedTicks: suggestedTicks as Record<string, unknown> | null,
      semantics: sem,
      xScale: sem?.x_scale === 'log' ? 'log' : 'linear',
      yScale: sem?.y_scale === 'log' ? 'log' : 'linear',
      step: 'calibrate',
    });
  },
  setChartType: (chartType) => set({ chartType }),
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
  setScale: (axis, scale) => set(axis === 'x' ? { xScale: scale } : { yScale: scale }),
  clearCalib: () => set({ xRefs: [], yRefs: [], calibAxis: 'x' }),
  setHeatmapOptions: (heatmapOptions) => set({ heatmapOptions }),
  setExtraction: (data, calibration) => {
    const series = ((data.series as SeriesData[]) || []).map((s) => ({
      ...s,
      pixel_points: s.pixel_points || [],
    }));
    set({
      series,
      fitCurves: (data.fit_curves as Array<Record<string, unknown>>) || [],
      flags: (data.low_confidence_flags as string[]) || [],
      overallConfidence: (data.overall_confidence as number) || 0,
      calibration,
      step: 'review',
    });
  },
  updatePoint: (si, pi, data, pixel) =>
    set((state) => {
      const series = state.series.map((ser, i) => {
        if (i !== si) return ser;
        return {
          ...ser,
          points: ser.points.map((pt, j) => (j === pi ? data : pt)),
          pixel_points: ser.pixel_points.map((pt, j) => (j === pi ? pixel : pt)),
        };
      });
      return { series };
    }),
  reset: () => set({ ...initial, locale: get().locale }),
}));

const ALLOWED = new Set<ChartTypeId>(['line', 'scatter', 'bar', 'heatmap', 'box']);

export function normalizeChartType(raw: string): ChartTypeId {
  return ALLOWED.has(raw as ChartTypeId) ? (raw as ChartTypeId) : 'line';
}

export function buildCalibration(
  xRefs: CalibPoint[],
  yRefs: CalibPoint[],
  xScale: 'linear' | 'log',
  yScale: 'linear' | 'log'
): CalibrationConfigPayload | null {
  if (xRefs.length < 2 || yRefs.length < 2) return null;
  return {
    x_axis: { scale: xScale, ref1: xRefs[0], ref2: xRefs[1] },
    y_axis: { scale: yScale, ref1: yRefs[0], ref2: yRefs[1] },
  };
}
