import { type TranslationKey, t } from '../i18n/translations';
import { useStore } from '../store/useStore';

const BASE = '/api';

function errMsg(key: TranslationKey): string {
  return t(useStore.getState().locale, key);
}

async function responseError(res: Response, key: TranslationKey): Promise<Error> {
  try {
    const data = await res.json();
    if (typeof data.detail === 'string') return new Error(data.detail);
  } catch {
    /* fall back to localized message */
  }
  return new Error(errMsg(key));
}

export type PdfPageInfo = { page: number; width: number; height: number };

export type UploadResponse = {
  image_id: string;
  url: string;
  source_type?: 'image' | 'pdf';
  source_id?: string;
  selected_page?: number;
  pages?: PdfPageInfo[];
};

export async function uploadImage(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/projects/upload`, { method: 'POST', body: form });
  if (!res.ok) throw await responseError(res, 'errUpload');
  return res.json();
}

export async function selectPdfPage(sourceId: string, page: number): Promise<UploadResponse> {
  const res = await fetch(`${BASE}/projects/pdf-page`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_id: sourceId, page }),
  });
  if (!res.ok) throw await responseError(res, 'errUpload');
  return res.json();
}

export type AnalyzeOptionsPayload = {
  chart_type_override?: string;
  use_vlm_regions?: boolean;
  force_redetect_plot?: boolean;
};

export async function autoAnalyze(imageId: string, options?: AnalyzeOptionsPayload) {
  const res = await fetch(`${BASE}/extract/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_id: imageId,
      options: options
        ? {
            chart_type_override: options.chart_type_override || null,
            use_vlm_regions: options.use_vlm_regions ?? true,
            force_redetect_plot: options.force_redetect_plot ?? false,
          }
        : undefined,
    }),
  });
  if (!res.ok) throw await responseError(res, 'errAnalyze');
  return res.json();
}

export async function extractCases(payload: Record<string, unknown>) {
  const res = await fetch(`${BASE}/extract/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await responseError(res, 'errExtract');
  return res.json();
}

export async function extractData(payload: Record<string, unknown>) {
  const res = await fetch(`${BASE}/extract/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await responseError(res, 'errExtract');
  return res.json();
}

export async function autoCalibrate(imageId: string, useVlm = true) {
  const res = await fetch(`${BASE}/calibrate/auto`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId, use_vlm: useVlm }),
  });
  if (!res.ok) throw await responseError(res, 'errAutoCalib');
  return res.json();
}

export async function recomputePoint(payload: {
  calibration: unknown;
  pixel_points: Array<{
    series_idx: number;
    point_idx: number;
    px: number;
    py: number;
  }>;
}) {
  const res = await fetch(`${BASE}/calibrate/recompute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await responseError(res, 'errRecompute');
  return res.json() as Promise<{
    points: Array<{
      series_idx: number;
      point_idx: number;
      x: number;
      y: number;
      px: number;
      py: number;
    }>;
  }>;
}

export async function exportResult(
  imageId: string,
  format: 'csv' | 'json' | 'excel' | 'pdf',
  result: unknown
) {
  const res = await fetch(`${BASE}/export/${imageId}?format=${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ result }),
  });
  if (!res.ok) throw await responseError(res, 'errExport');
  return res.blob();
}
