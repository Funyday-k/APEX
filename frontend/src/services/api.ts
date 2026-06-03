import { type TranslationKey, t } from '../i18n/translations';
import { useStore } from '../store/useStore';

const BASE = '/api';

function errMsg(key: TranslationKey): string {
  return t(useStore.getState().locale, key);
}

export async function uploadImage(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/projects/upload`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(errMsg('errUpload'));
  return res.json() as Promise<{ image_id: string; url: string }>;
}

export async function autoAnalyze(imageId: string) {
  const res = await fetch(`${BASE}/extract/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId }),
  });
  if (!res.ok) throw new Error(errMsg('errAnalyze'));
  return res.json();
}

export async function extractData(payload: Record<string, unknown>) {
  const res = await fetch(`${BASE}/extract/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || errMsg('errExtract'));
  }
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
  if (!res.ok) throw new Error(errMsg('errRecompute'));
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
  series: unknown[]
) {
  const res = await fetch(`${BASE}/export/${imageId}?format=${format}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ series }),
  });
  if (!res.ok) throw new Error(errMsg('errExport'));
  return res.blob();
}
