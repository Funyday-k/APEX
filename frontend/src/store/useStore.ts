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
export type ImageGeometry = { natural: Pixel; display: Pixel };

export type PixelDisplayMode = 'data' | 'detected';

export type SeriesData = {
  name: string;
  color_hex?: string;
  points: { x: number; y: number }[];
  pixel_points: Pixel[];
  detected_pixel_points?: Pixel[];
  confidence?: number;
  has_error_bars?: boolean;
  errors?: unknown[];
};

export type ChartMetadata = {
  title?: string | null;
  x_label?: string | null;
  y_label?: string | null;
  x_quantity?: string | null;
  y_quantity?: string | null;
  x_unit?: string | null;
  y_unit?: string | null;
  legend?: string[];
};

export type PlotRegionsPayload = {
  regions: Array<{
    kind: string;
    bbox: { x0: number; y0: number; x1: number; y1: number };
    label?: string | null;
  }>;
  image_width?: number;
  image_height?: number;
};

export type SuggestedRemoval = {
  series_idx: number;
  point_idx: number;
  pixel_x: number;
  pixel_y: number;
  reason: string;
  confidence: number;
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
  imageGeometry: ImageGeometry | null;

  chartType: ChartTypeId;
  suggestedTicks: Record<string, unknown> | null;
  semantics: Record<string, unknown> | null;
  regions: PlotRegionsPayload | null;
  chartMetadata: ChartMetadata | null;
  suggestedRemovals: SuggestedRemoval[];

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
  pixelDisplayMode: PixelDisplayMode;
  showFitCurves: boolean;

  setLocale: (locale: Locale) => void;
  setStep: (s: Step) => void;
  setLoading: (b: boolean, msg?: string) => void;
  setError: (msg: string | null) => void;
  setImage: (url: string, id: string) => void;
  setImageGeometry: (natural: Pixel) => void;
  setAnalysis: (
    chartType: string,
    ticks: unknown,
    semantics: unknown,
    regions?: unknown,
    chartMetadata?: unknown
  ) => void;
  setChartType: (t: ChartTypeId) => void;
  addCalibPoint: (p: CalibPoint) => void;
  setCalibAxis: (a: 'x' | 'y') => void;
  setScale: (axis: 'x' | 'y', scale: 'linear' | 'log') => void;
  clearCalib: () => void;
  setHeatmapOptions: (o: State['heatmapOptions']) => void;
  setExtraction: (data: Record<string, unknown>, cal: CalibrationConfigPayload) => void;
  updatePoint: (si: number, pi: number, data: { x: number; y: number }, pixel: Pixel) => void;
  removePoint: (si: number, pi: number) => void;
  applySuggestedRemovals: () => void;
  showRegionOverlay: boolean;
  setShowRegionOverlay: (show: boolean) => void;
  setPixelDisplayMode: (mode: PixelDisplayMode) => void;
  setShowFitCurves: (show: boolean) => void;
  applySuggestedCalibration: () => void;
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
  imageGeometry: null,
  chartType: 'line' as ChartTypeId,
  suggestedTicks: null,
  semantics: null,
  regions: null,
  chartMetadata: null,
  suggestedRemovals: [] as SuggestedRemoval[],
  showRegionOverlay: true,
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
  pixelDisplayMode: 'data' as PixelDisplayMode,
  showFitCurves: true,
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
    set({
      imageUrl,
      imageId,
      imageGeometry: null,
      step: 'analyze',
      error: null,
      xRefs: [],
      yRefs: [],
    }),
  setImageGeometry: (natural) =>
    set({
      imageGeometry: {
        natural,
        display: fitImageSize(natural.x, natural.y),
      },
    }),
  setAnalysis: (chartType, suggestedTicks, semantics, regions, chartMetadata) => {
    const sem = semantics as Record<string, unknown> | null;
    const meta =
      (chartMetadata as ChartMetadata | null) ||
      (sem
        ? {
            title: sem.title as string | null,
            x_label: sem.x_label as string | null,
            y_label: sem.y_label as string | null,
            x_quantity: sem.x_quantity as string | null,
            y_quantity: sem.y_quantity as string | null,
            x_unit: sem.x_unit as string | null,
            y_unit: sem.y_unit as string | null,
            legend: (sem.legend as string[]) || [],
          }
        : null);
    set({
      chartType: normalizeChartType(chartType),
      suggestedTicks: suggestedTicks as Record<string, unknown> | null,
      semantics: sem,
      regions: (regions as PlotRegionsPayload | null) || null,
      chartMetadata: meta,
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
    const geometry = get().imageGeometry;
    const mapPx = (pts: Pixel[] | undefined) =>
      (pts || []).map((p) => (geometry ? naturalToDisplay(p, geometry) : p));
    const series = ((data.series as SeriesData[]) || []).map((s) => ({
      ...s,
      pixel_points: mapPx(s.pixel_points),
      detected_pixel_points: mapPx(s.detected_pixel_points),
    }));
    const removals = ((data.suggested_removals as SuggestedRemoval[]) || []).map((r) => ({
      ...r,
      pixel_x: geometry ? naturalToDisplay({ x: r.pixel_x, y: r.pixel_y }, geometry).x : r.pixel_x,
      pixel_y: geometry ? naturalToDisplay({ x: r.pixel_x, y: r.pixel_y }, geometry).y : r.pixel_y,
    }));
    const cm = data.chart_metadata as ChartMetadata | undefined;
    set({
      series,
      fitCurves: (data.fit_curves as Array<Record<string, unknown>>) || [],
      flags: (data.low_confidence_flags as string[]) || [],
      overallConfidence: (data.overall_confidence as number) || 0,
      calibration,
      suggestedRemovals: removals,
      chartMetadata: cm || get().chartMetadata,
      regions: (data.regions as PlotRegionsPayload) || get().regions,
      pixelDisplayMode: 'data',
      showFitCurves: true,
      step: 'review',
    });
  },
  applySuggestedRemovals: () => {
    const { suggestedRemovals } = get();
    if (!suggestedRemovals.length) return;
    const sorted = [...suggestedRemovals].sort((a, b) => {
      if (a.series_idx !== b.series_idx) return b.series_idx - a.series_idx;
      return b.point_idx - a.point_idx;
    });
    for (const r of sorted) {
      get().removePoint(r.series_idx, r.point_idx);
    }
    set({ suggestedRemovals: [] });
  },
  setShowRegionOverlay: (showRegionOverlay) => set({ showRegionOverlay }),
  removePoint: (si, pi) =>
    set((state) => ({
      series: state.series.map((ser, i) => {
        if (i !== si) return ser;
        return {
          ...ser,
          points: ser.points.filter((_, j) => j !== pi),
          pixel_points: ser.pixel_points.filter((_, j) => j !== pi),
          detected_pixel_points: ser.detected_pixel_points?.filter((_, j) => j !== pi),
          errors: ser.errors?.filter((_, j) => j !== pi),
        };
      }),
    })),
  setPixelDisplayMode: (pixelDisplayMode) => set({ pixelDisplayMode }),
  setShowFitCurves: (showFitCurves) => set({ showFitCurves }),
  applySuggestedCalibration: () => {
    const { suggestedTicks, imageGeometry } = get();
    if (!suggestedTicks || !imageGeometry) return;
    const xt = (suggestedTicks.x_ticks as Array<{ pixel: number; value: number }>) || [];
    const yt = (suggestedTicks.y_ticks as Array<{ pixel: number; value: number }>) || [];
    if (xt.length < 2 || yt.length < 2) return;
    const xRefs: CalibPoint[] = xt.slice(0, 2).map((t) => ({
      pixel: naturalToDisplay({ x: t.pixel, y: 0 }, imageGeometry),
      data: { x: t.value, y: 0 },
    }));
    const yRefs: CalibPoint[] = yt.slice(0, 2).map((t) => ({
      pixel: naturalToDisplay({ x: 0, y: t.pixel }, imageGeometry),
      data: { x: 0, y: t.value },
    }));
    set({ xRefs, yRefs, calibAxis: 'x' });
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
  yScale: 'linear' | 'log',
  geometry?: ImageGeometry | null
): CalibrationConfigPayload | null {
  if (xRefs.length < 2 || yRefs.length < 2) return null;
  const mapPoint = (p: CalibPoint): CalibPoint => ({
    ...p,
    pixel: geometry ? displayToNatural(p.pixel, geometry) : p.pixel,
  });
  return {
    x_axis: { scale: xScale, ref1: mapPoint(xRefs[0]), ref2: mapPoint(xRefs[1]) },
    y_axis: { scale: yScale, ref1: mapPoint(yRefs[0]), ref2: mapPoint(yRefs[1]) },
  };
}

export function fitImageSize(naturalWidth: number, naturalHeight: number): Pixel {
  const fit = Math.min(900 / naturalWidth, 650 / naturalHeight, 1);
  return {
    x: naturalWidth * fit,
    y: naturalHeight * fit,
  };
}

export function displayToNatural(point: Pixel, geometry: ImageGeometry): Pixel {
  return mapPointBetweenSizes(point, geometry.display, geometry.natural);
}

export function naturalToDisplay(point: Pixel, geometry: ImageGeometry): Pixel {
  return mapPointBetweenSizes(point, geometry.natural, geometry.display);
}

function mapPointBetweenSizes(point: Pixel, from: Pixel, to: Pixel): Pixel {
  return {
    x: from.x === 0 ? point.x : (point.x * to.x) / from.x,
    y: from.y === 0 ? point.y : (point.y * to.y) / from.y,
  };
}
