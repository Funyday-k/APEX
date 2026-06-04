import { create } from 'zustand';
import type { Locale } from '../i18n/translations';
import {
  displayToNatural as displayToNaturalCoord,
  naturalToDisplay as naturalToDisplayCoord,
} from '../utils/canvasCoords';
import { normalizeRegionsToImage } from '../utils/regions';

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
  x_scale?: string;
  y_scale?: string;
  legend?: string[];
};

export type PlotRegionsPayload = {
  regions: Array<{
    kind: string;
    bbox: { x0: number; y0: number; x1: number; y1: number; confidence?: number };
    label?: string | null;
    source?: string | null;
  }>;
  image_width?: number;
  image_height?: number;
  source?: string;
};

export type AxisGeometry = {
  x_axis: { y_pixel: number; x_start: number; x_end: number; confidence?: number };
  y_axis: { x_pixel: number; y_start: number; y_end: number; confidence?: number };
};

export type AxisConfidence = {
  x_axis?: number;
  y_axis?: number;
  plot_area?: number;
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

export type ImageInfo = {
  fileName?: string;
  fileSize?: number;
  mimeType?: string;
  width?: number;
  height?: number;
  imageId?: string;
  regionCount?: number;
};

export type AnalyzeOptionsState = {
  chart_type_override: string;
  use_vlm_regions: boolean;
  force_redetect_plot: boolean;
};

export type ExtractOptionsState = {
  color_tolerance: number;
  min_marker_area: number;
  suppress_grid: boolean;
  intersect_auto: boolean;
  enable_vlm_audit: boolean;
  enable_ai_evaluation: boolean;
};

type State = {
  locale: Locale;
  step: Step;
  loading: boolean;
  loadingMsg: string;
  error: string | null;

  imageUrl: string | null;
  imageId: string | null;
  imageInfo: ImageInfo | null;
  imageGeometry: ImageGeometry | null;

  chartType: ChartTypeId;
  suggestedTicks: Record<string, unknown> | null;
  axisGeometry: AxisGeometry | null;
  axisConfidence: AxisConfidence | null;
  semantics: Record<string, unknown> | null;
  regions: PlotRegionsPayload | null;
  chartMetadata: ChartMetadata | null;
  suggestedRemovals: SuggestedRemoval[];
  analysisDone: boolean;
  analysisSnapshot: Record<string, unknown> | null;
  autoCalibConfidence: number;
  autoCalibPending: boolean;
  maxStepReached: Step;
  analyzeOptions: AnalyzeOptionsState;
  extractOptions: ExtractOptionsState;
  reviewMainView: 'source' | 'rebuilt';
  aiEvaluationScore: number | null;

  xRefs: CalibPoint[];
  yRefs: CalibPoint[];
  xScale: 'linear' | 'log';
  yScale: 'linear' | 'log';
  calibAxis: 'x' | 'y';
  selectedCalib: { axis: 'x' | 'y'; index: number } | null;

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
  goToStep: (s: Step) => void;
  setLoading: (b: boolean, msg?: string) => void;
  setError: (msg: string | null) => void;
  setImage: (url: string, id: string, fileMeta?: Partial<ImageInfo>) => void;
  syncRegionsToImageSize: (width: number, height: number) => void;
  setImageGeometry: (natural: Pixel) => void;
  setAnalysis: (res: Record<string, unknown>) => void;
  setAnalyzeOptions: (o: Partial<AnalyzeOptionsState>) => void;
  setExtractOptions: (o: Partial<ExtractOptionsState>) => void;
  setReviewMainView: (v: 'source' | 'rebuilt') => void;
  setChartType: (t: ChartTypeId) => void;
  addCalibPoint: (p: CalibPoint) => void;
  updateCalibPoint: (axis: 'x' | 'y', index: number, pixel: Pixel) => void;
  setSelectedCalib: (sel: { axis: 'x' | 'y'; index: number } | null) => void;
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
  applySuggestedCalibrationConfig: (config: Record<string, unknown>) => void;
  reset: () => void;
};

const defaultAnalyzeOptions: AnalyzeOptionsState = {
  chart_type_override: '',
  use_vlm_regions: true,
  force_redetect_plot: false,
};

const defaultExtractOptions: ExtractOptionsState = {
  color_tolerance: 30,
  min_marker_area: 8,
  suppress_grid: true,
  intersect_auto: true,
  enable_vlm_audit: true,
  enable_ai_evaluation: true,
};

const STEP_ORDER: Step[] = ['upload', 'analyze', 'calibrate', 'extract', 'review'];

function stepRank(s: Step): number {
  return STEP_ORDER.indexOf(s);
}

const initial = {
  locale: loadLocale(),
  step: 'upload' as Step,
  loading: false,
  loadingMsg: '',
  error: null,
  imageUrl: null,
  imageId: null,
  imageInfo: null,
  imageGeometry: null,
  chartType: 'line' as ChartTypeId,
  suggestedTicks: null,
  axisGeometry: null,
  axisConfidence: null,
  semantics: null,
  regions: null,
  chartMetadata: null,
  suggestedRemovals: [] as SuggestedRemoval[],
  analysisDone: false,
  analysisSnapshot: null,
  autoCalibConfidence: 0,
  autoCalibPending: false,
  maxStepReached: 'upload' as Step,
  analyzeOptions: defaultAnalyzeOptions,
  extractOptions: defaultExtractOptions,
  reviewMainView: 'source' as const,
  aiEvaluationScore: null,
  showRegionOverlay: true,
  xRefs: [] as CalibPoint[],
  yRefs: [] as CalibPoint[],
  xScale: 'linear' as const,
  yScale: 'linear' as const,
  calibAxis: 'x' as const,
  selectedCalib: null as { axis: 'x' | 'y'; index: number } | null,
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
  setStep: (step) =>
    set((state) => ({
      step,
      error: null,
      maxStepReached:
        stepRank(step) > stepRank(state.maxStepReached) ? step : state.maxStepReached,
    })),
  goToStep: (step) => {
    const { maxStepReached } = get();
    if (stepRank(step) <= stepRank(maxStepReached)) {
      get().setStep(step);
    }
  },
  setLoading: (loading, loadingMsg = '') => set({ loading, loadingMsg }),
  setError: (error) => set({ error }),
  setImage: (imageUrl, imageId, fileMeta) =>
    set({
      imageUrl,
      imageId,
      imageGeometry: null,
      regions: null,
      axisGeometry: null,
      axisConfidence: null,
      chartMetadata: null,
      semantics: null,
      step: 'analyze',
      error: null,
      analysisDone: false,
      maxStepReached: 'analyze',
      xRefs: [],
      yRefs: [],
      imageInfo: {
        imageId,
        fileName: fileMeta?.fileName,
        fileSize: fileMeta?.fileSize,
        mimeType: fileMeta?.mimeType,
        width: fileMeta?.width,
        height: fileMeta?.height,
      },
    }),
  syncRegionsToImageSize: (width, height) => {
    const { regions, imageInfo } = get();
    const normalized = normalizeRegionsToImage(regions, width, height);
    if (normalized === regions) {
      set({
        imageInfo: imageInfo
          ? { ...imageInfo, width, height, regionCount: regions?.regions?.length ?? 0 }
          : { width, height, regionCount: regions?.regions?.length ?? 0 },
      });
      return;
    }
    set({
      regions: normalized,
      imageInfo: imageInfo
        ? {
            ...imageInfo,
            width,
            height,
            regionCount: normalized?.regions?.length ?? 0,
          }
        : { width, height, regionCount: normalized?.regions?.length ?? 0 },
    });
  },
  setImageGeometry: (natural) => {
    get().syncRegionsToImageSize(natural.x, natural.y);
    set({
      imageGeometry: {
        natural,
        display: fitImageSize(natural.x, natural.y),
      },
    });
  },
  setAnalysis: (res) => {
    const chartType = res.chart_type as string;
    const suggestedTicks = res.suggested_calibration;
    const semantics = res.semantics;
    const regions = res.regions;
    const chartMetadata = res.chart_metadata;
    const axisGeometry = res.axis_geometry;
    const axisConfidence = res.axis_confidence;
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
    const snap = res.analysis_snapshot as Record<string, unknown> | undefined;
    const iw = snap?.image_width as number | undefined;
    const ih = snap?.image_height as number | undefined;
    const geometry = get().imageGeometry;
    let normalizedRegions = (regions as PlotRegionsPayload | null) || null;
    if (normalizedRegions && geometry) {
      normalizedRegions = normalizeRegionsToImage(
        normalizedRegions,
        geometry.natural.x,
        geometry.natural.y
      );
    } else if (normalizedRegions && iw && ih) {
      normalizedRegions = normalizeRegionsToImage(normalizedRegions, iw, ih);
    }
    const regionCount = normalizedRegions?.regions?.length ?? 0;
    const autoConf = (res.auto_calibration_confidence as number) || 0;
    const suggestedConfig = res.suggested_calibration_config as Record<string, unknown> | null;
    const autoApplied = Boolean(res.auto_calibration_applied);

    const updates: Partial<State> = {
      chartType: normalizeChartType(chartType),
      suggestedTicks: suggestedTicks as Record<string, unknown> | null,
      axisGeometry: (axisGeometry as AxisGeometry | null) || null,
      axisConfidence: (axisConfidence as AxisConfidence | null) || null,
      semantics: sem,
      regions: normalizedRegions,
      chartMetadata: meta,
      analysisDone: true,
      analysisSnapshot: snap || null,
      autoCalibConfidence: autoConf,
      autoCalibPending: !autoApplied && Boolean(suggestedConfig),
      xScale:
        (meta as { x_scale?: string } | null)?.x_scale === 'log' ||
        sem?.x_scale === 'log'
          ? 'log'
          : 'linear',
      yScale:
        (meta as { y_scale?: string } | null)?.y_scale === 'log' ||
        sem?.y_scale === 'log'
          ? 'log'
          : 'linear',
      step: 'analyze',
      maxStepReached: 'analyze',
      imageInfo: get().imageInfo
        ? {
            ...get().imageInfo!,
            regionCount,
            width: get().imageInfo!.width || iw,
            height: get().imageInfo!.height || ih,
          }
        : iw && ih
          ? { width: iw, height: ih, regionCount }
          : regionCount
            ? { regionCount }
            : get().imageInfo,
    };

    set(updates);

    if (autoApplied && suggestedConfig) {
      get().applySuggestedCalibrationConfig(suggestedConfig);
    } else if (suggestedConfig && autoConf >= 0.55) {
      get().applySuggestedCalibrationConfig(suggestedConfig);
    }
  },
  setAnalyzeOptions: (o) =>
    set((state) => ({ analyzeOptions: { ...state.analyzeOptions, ...o } })),
  setExtractOptions: (o) =>
    set((state) => ({ extractOptions: { ...state.extractOptions, ...o } })),
  setReviewMainView: (reviewMainView) => set({ reviewMainView }),
  setChartType: (chartType) => set({ chartType }),
  addCalibPoint: (p) => {
    const { calibAxis, xRefs, yRefs } = get();
    if (calibAxis === 'x') {
      const next = [...xRefs, p].slice(-2);
      set({ xRefs: next, calibAxis: next.length >= 2 ? 'y' : 'x', selectedCalib: null });
    } else {
      set({ yRefs: [...yRefs, p].slice(-2), selectedCalib: null });
    }
  },
  updateCalibPoint: (axis, index, pixel) => {
    const { xRefs, yRefs, axisGeometry } = get();
    const snap = { x: Math.round(pixel.x), y: Math.round(pixel.y) };
    if (axis === 'x') {
      const next = xRefs.map((r, i) => {
        if (i !== index) return r;
        const y =
          axisGeometry?.x_axis?.y_pixel != null
            ? axisGeometry.x_axis.y_pixel
            : snap.y;
        return { pixel: { x: snap.x, y }, data: r.data };
      });
      set({ xRefs: next });
    } else {
      const next = yRefs.map((r, i) => {
        if (i !== index) return r;
        const x =
          axisGeometry?.y_axis?.x_pixel != null
            ? axisGeometry.y_axis.x_pixel
            : snap.x;
        return { pixel: { x, y: snap.y }, data: r.data };
      });
      set({ yRefs: next });
    }
  },
  setSelectedCalib: (selectedCalib) => set({ selectedCalib }),
  setCalibAxis: (calibAxis) => set({ calibAxis }),
  setScale: (axis, scale) => set(axis === 'x' ? { xScale: scale } : { yScale: scale }),
  clearCalib: () => set({ xRefs: [], yRefs: [], calibAxis: 'x', selectedCalib: null }),
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
      maxStepReached: 'review',
      reviewMainView: 'source',
      aiEvaluationScore: (data.ai_evaluation_score as number) ?? null,
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
    const { suggestedTicks, axisGeometry } = get();
    if (!suggestedTicks) return;
    const xt = (suggestedTicks.x_ticks as Array<{ pixel: number; value: number }>) || [];
    const yt = (suggestedTicks.y_ticks as Array<{ pixel: number; value: number }>) || [];
    if (xt.length < 2 || yt.length < 2) return;
    const xAxisY = axisGeometry?.x_axis?.y_pixel ?? 0;
    const yAxisX = axisGeometry?.y_axis?.x_pixel ?? 0;
    const sortedX = [...xt].sort((a, b) => a.pixel - b.pixel);
    const sortedY = [...yt].sort((a, b) => a.pixel - b.pixel);
    const xRefs: CalibPoint[] = [sortedX[0], sortedX[sortedX.length - 1]].map((t) => ({
      pixel: { x: t.pixel, y: xAxisY },
      data: { x: t.value, y: 0 },
    }));
    const yRefs: CalibPoint[] = [sortedY[0], sortedY[sortedY.length - 1]].map((t) => ({
      pixel: { x: yAxisX, y: t.pixel },
      data: { x: 0, y: t.value },
    }));
    set({ xRefs, yRefs, calibAxis: 'x', autoCalibPending: false });
  },
  applySuggestedCalibrationConfig: (config) => {
    type Ref = { pixel: Pixel; data: Pixel };
    const parseRef = (r: unknown): CalibPoint | null => {
      if (!r || typeof r !== 'object') return null;
      const o = r as { pixel?: Pixel; data?: Pixel };
      if (!o.pixel || !o.data) return null;
      return { pixel: o.pixel, data: o.data };
    };
    const xa = config.x_axis as { scale?: string; ref1?: Ref; ref2?: Ref } | undefined;
    const ya = config.y_axis as { scale?: string; ref1?: Ref; ref2?: Ref } | undefined;
    const r1x = parseRef(xa?.ref1);
    const r2x = parseRef(xa?.ref2);
    const r1y = parseRef(ya?.ref1);
    const r2y = parseRef(ya?.ref2);
    if (!r1x || !r2x || !r1y || !r2y) return;
    set({
      xRefs: [r1x, r2x],
      yRefs: [r1y, r2y],
      xScale: xa?.scale === 'log' ? 'log' : 'linear',
      yScale: ya?.scale === 'log' ? 'log' : 'linear',
      calibAxis: 'x',
      autoCalibPending: false,
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

export function fitImageSize(naturalWidth: number, naturalHeight: number): Pixel {
  const fit = Math.min(900 / naturalWidth, 650 / naturalHeight, 1);
  return {
    x: naturalWidth * fit,
    y: naturalHeight * fit,
  };
}

export function displayToNatural(point: Pixel, geometry: ImageGeometry): Pixel {
  return displayToNaturalCoord(point, geometry);
}

export function naturalToDisplay(point: Pixel, geometry: ImageGeometry): Pixel {
  return naturalToDisplayCoord(point, geometry);
}
