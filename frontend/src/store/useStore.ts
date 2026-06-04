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
  representation?: string;
  error_band?: unknown;
};

export type PdfPageInfo = { page: number; width: number; height: number };

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

export type ExtractionCase = {
  label: string;
  color_hex: string;
  representation: 'line' | 'scatter' | 'band';
  sub_bbox?: { x0: number; y0: number; x1: number; y1: number };
  notes?: string;
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
  aiCalibSource: 'vlm' | 'cv' | null;
  aiCalibDiagnostics: Record<string, unknown> | null;
  maxStepReached: Step;
  selectedRegionIndex: number | null;
  newRegionKind: string;
  canvasScale: number;
  canvasStagePos: { x: number; y: number };
  canvasViewport: { w: number; h: number };
  canvasFitScale: number;
  canvasPanMode: boolean;
  regionAdjustOpen: boolean;
  calibAttempted: boolean;
  cases: ExtractionCase[];
  analyzeOptions: AnalyzeOptionsState;
  extractOptions: ExtractOptionsState;
  reviewMainView: 'source' | 'rebuilt';
  aiEvaluationScore: number | null;

  sourceType: 'image' | 'pdf';
  sourceId: string | null;
  pdfPages: PdfPageInfo[];
  selectedPdfPage: number;
  regionsConfirmed: boolean;

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
  errorBands: Array<Record<string, unknown>>;
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
  setSourceMeta: (meta: {
    sourceType?: 'image' | 'pdf';
    sourceId?: string | null;
    pdfPages?: PdfPageInfo[];
    selectedPdfPage?: number;
  }) => void;
  setRegions: (regions: PlotRegionsPayload | null) => void;
  setSelectedRegionIndex: (index: number | null) => void;
  setNewRegionKind: (kind: string) => void;
  updateRegion: (
    index: number,
    bbox: { x0: number; y0: number; x1: number; y1: number }
  ) => void;
  addRegion: (kind: string) => void;
  deleteRegion: (index: number) => void;
  setRegionKind: (index: number, kind: string) => void;
  setCanvasViewport: (w: number, h: number) => void;
  setCanvasScale: (scale: number) => void;
  setCanvasStagePos: (pos: { x: number; y: number }) => void;
  setCanvasFitScale: (scale: number) => void;
  setCanvasPanMode: (on: boolean) => void;
  setRegionAdjustOpen: (open: boolean) => void;
  initCanvasView: () => void;
  resetCanvasView: () => void;
  fitCanvasToViewport: () => void;
  setCases: (cases: ExtractionCase[]) => void;
  updateCase: (index: number, patch: Partial<ExtractionCase>) => void;
  addCase: () => void;
  deleteCase: (index: number) => void;
  confirmRegions: () => void;
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
  runAiCalibrate: () => Promise<void>;
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
  aiCalibSource: null as 'vlm' | 'cv' | null,
  aiCalibDiagnostics: null as Record<string, unknown> | null,
  maxStepReached: 'upload' as Step,
  selectedRegionIndex: null as number | null,
  newRegionKind: 'legend',
  canvasScale: 1,
  canvasStagePos: { x: 0, y: 0 },
  canvasViewport: { w: 900, h: 650 },
  canvasFitScale: 1,
  canvasPanMode: false,
  regionAdjustOpen: false,
  calibAttempted: false,
  cases: [] as ExtractionCase[],
  analyzeOptions: defaultAnalyzeOptions,
  extractOptions: defaultExtractOptions,
  reviewMainView: 'source' as const,
  aiEvaluationScore: null,
  sourceType: 'image' as const,
  sourceId: null as string | null,
  pdfPages: [] as PdfPageInfo[],
  selectedPdfPage: 0,
  regionsConfirmed: false,
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
  errorBands: [] as Array<Record<string, unknown>>,
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
      regionsConfirmed: false,
      maxStepReached: 'analyze',
      xRefs: [],
      yRefs: [],
      calibAttempted: false,
      regionAdjustOpen: false,
      cases: [],
      canvasScale: 1,
      canvasStagePos: { x: 0, y: 0 },
      canvasPanMode: false,
      imageInfo: {
        imageId,
        fileName: fileMeta?.fileName,
        fileSize: fileMeta?.fileSize,
        mimeType: fileMeta?.mimeType,
        width: fileMeta?.width,
        height: fileMeta?.height,
      },
    }),
  setSourceMeta: (meta) =>
    set((state) => ({
      sourceType: meta.sourceType ?? state.sourceType,
      sourceId: meta.sourceId !== undefined ? meta.sourceId : state.sourceId,
      pdfPages: meta.pdfPages ?? state.pdfPages,
      selectedPdfPage: meta.selectedPdfPage ?? state.selectedPdfPage,
    })),
  setRegions: (regions) => set({ regions, regionsConfirmed: false }),
  setSelectedRegionIndex: (selectedRegionIndex) => set({ selectedRegionIndex }),
  setNewRegionKind: (newRegionKind) => set({ newRegionKind }),
  updateRegion: (index, bbox) => {
    const { regions } = get();
    if (!regions?.regions?.[index]) return;
    const next = regions.regions.map((r, i) =>
      i === index
        ? {
            ...r,
            bbox: { ...r.bbox, ...bbox },
            source: 'manual' as const,
          }
        : r
    );
    set({
      regions: { ...regions, regions: next },
      regionsConfirmed: false,
    });
  },
  addRegion: (kind) => {
    const { regions, imageGeometry } = get();
    if (!imageGeometry) return;
    const nw = imageGeometry.natural.x;
    const nh = imageGeometry.natural.y;
    const w = Math.round(nw * 0.2);
    const h = Math.round(nh * 0.12);
    const x0 = Math.round((nw - w) / 2);
    const y0 = Math.round((nh - h) / 2);
    const item = {
      kind,
      bbox: { x0, y0, x1: x0 + w, y1: y0 + h, confidence: 0.7 },
      source: 'manual' as const,
    };
    const base = regions || {
      regions: [],
      image_width: nw,
      image_height: nh,
      source: 'manual',
    };
    const nextRegions = [...base.regions, item];
    set({
      regions: {
        ...base,
        image_width: nw,
        image_height: nh,
        regions: nextRegions,
      },
      selectedRegionIndex: nextRegions.length - 1,
      regionsConfirmed: false,
    });
  },
  deleteRegion: (index) => {
    const { regions } = get();
    if (!regions) return;
    const next = regions.regions.filter((_, i) => i !== index);
    set({
      regions: { ...regions, regions: next },
      selectedRegionIndex: null,
      regionsConfirmed: false,
    });
  },
  setRegionKind: (index, kind) => {
    const { regions } = get();
    if (!regions?.regions[index]) return;
    const next = regions.regions.map((r, i) =>
      i === index ? { ...r, kind, source: 'manual' as const } : r
    );
    set({ regions: { ...regions, regions: next }, regionsConfirmed: false });
  },
  setCanvasViewport: (w, h) => set({ canvasViewport: { w, h } }),
  setCanvasScale: (canvasScale) => set({ canvasScale }),
  setCanvasStagePos: (canvasStagePos) => set({ canvasStagePos }),
  setCanvasFitScale: (canvasFitScale) => set({ canvasFitScale }),
  setCanvasPanMode: (canvasPanMode) => set({ canvasPanMode }),
  setRegionAdjustOpen: (regionAdjustOpen) => set({ regionAdjustOpen }),
  initCanvasView: () => {
    const { canvasViewport, imageGeometry } = get();
    if (!imageGeometry) return;
    const pos = {
      x: Math.max(0, (canvasViewport.w - imageGeometry.display.x) / 2),
      y: Math.max(0, (canvasViewport.h - imageGeometry.display.y) / 2),
    };
    set({
      canvasScale: 1,
      canvasFitScale: 1,
      canvasStagePos: pos,
    });
  },
  resetCanvasView: () => {
    const { canvasViewport, imageGeometry } = get();
    if (!imageGeometry) {
      set({ canvasScale: 1, canvasStagePos: { x: 0, y: 0 } });
      return;
    }
    const pos = {
      x: Math.max(0, (canvasViewport.w - imageGeometry.display.x) / 2),
      y: Math.max(0, (canvasViewport.h - imageGeometry.display.y) / 2),
    };
    set({ canvasScale: 1, canvasStagePos: pos });
  },
  fitCanvasToViewport: () => {
    const { canvasViewport, imageGeometry } = get();
    if (!imageGeometry) return;
    const fit = Math.min(
      canvasViewport.w / imageGeometry.display.x,
      canvasViewport.h / imageGeometry.display.y,
      1
    );
    const sw = imageGeometry.display.x * fit;
    const sh = imageGeometry.display.y * fit;
    set({
      canvasFitScale: fit,
      canvasScale: fit,
      canvasStagePos: {
        x: Math.max(0, (canvasViewport.w - sw) / 2),
        y: Math.max(0, (canvasViewport.h - sh) / 2),
      },
    });
  },
  setCases: (cases) => set({ cases }),
  updateCase: (index, patch) => {
    const { cases } = get();
    const next = cases.map((c, i) => (i === index ? { ...c, ...patch } : c));
    set({ cases: next });
  },
  addCase: () => {
    const { cases } = get();
    set({
      cases: [
        ...cases,
        {
          label: `case ${cases.length + 1}`,
          color_hex: '#3388ff',
          representation: 'scatter',
        },
      ],
    });
  },
  deleteCase: (index) => {
    set({ cases: get().cases.filter((_, i) => i !== index) });
  },
  confirmRegions: () => set({ regionsConfirmed: true }),
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
    const rawCases = res.cases;
    const parsedCases: ExtractionCase[] = Array.isArray(rawCases)
      ? (rawCases as ExtractionCase[]).map((c, i) => ({
          label: String((c as ExtractionCase).label || `case ${i + 1}`),
          color_hex: String((c as ExtractionCase).color_hex || '#3388ff'),
          representation:
            (c as ExtractionCase).representation === 'line' ||
            (c as ExtractionCase).representation === 'band'
              ? (c as ExtractionCase).representation
              : 'scatter',
          sub_bbox: (c as ExtractionCase).sub_bbox,
          notes: (c as ExtractionCase).notes,
        }))
      : [];

    const updates: Partial<State> = {
      chartType: normalizeChartType(chartType),
      cases: parsedCases,
      suggestedTicks: suggestedTicks as Record<string, unknown> | null,
      axisGeometry: (axisGeometry as AxisGeometry | null) || null,
      axisConfidence: (axisConfidence as AxisConfidence | null) || null,
      semantics: sem,
      regions: normalizedRegions,
      chartMetadata: meta,
      analysisDone: true,
      regionsConfirmed: false,
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
    } else if (suggestedConfig && autoConf >= 0.65) {
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
      errorBands: (data.error_bands as Array<Record<string, unknown>>) || [],
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
  runAiCalibrate: async () => {
    const { imageId, locale } = get();
    if (!imageId) return;
    const { autoCalibrate } = await import('../services/api');
    set({
      loading: true,
      loadingMsg: locale === 'zh' ? 'AI 标定中…' : 'AI calibrating…',
    });
    set({ error: null });
    try {
      const res = await autoCalibrate(imageId, true);
      const cfg = res.suggested_calibration_config as Record<string, unknown> | null;
      if (cfg) {
        get().applySuggestedCalibrationConfig(cfg);
      }
      set({
        autoCalibConfidence: (res.auto_confidence as number) || 0,
        autoCalibPending: false,
        aiCalibSource: (res.source as 'vlm' | 'cv') || null,
        aiCalibDiagnostics: (res.calibration_diagnostics as Record<string, unknown>) || null,
        axisGeometry: (res.axis_geometry as AxisGeometry) || get().axisGeometry,
        suggestedTicks: (res.ticks as Record<string, unknown>) || get().suggestedTicks,
      });
    } catch (e) {
      set({ error: (e as Error).message });
    } finally {
      set({ loading: false, loadingMsg: '' });
    }
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
