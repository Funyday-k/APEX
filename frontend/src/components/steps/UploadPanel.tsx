import { useRef, useState } from 'react';
import { useT } from '../../i18n/useT';
import { autoAnalyze, selectPdfPage, uploadImage } from '../../services/api';
import { useStore } from '../../store/useStore';

export function UploadPanel() {
  const fileRef = useRef<HTMLInputElement>(null);
  const {
    setImage,
    setSourceMeta,
    setAnalysis,
    setLoading,
    setError,
    analyzeOptions,
    pdfPages,
    sourceId,
    selectedPdfPage,
    sourceType,
  } = useStore();
  const { t } = useT();
  const [pendingPdfSelect, setPendingPdfSelect] = useState(false);

  const readDimensions = (file: File): Promise<{ width?: number; height?: number }> =>
    new Promise((resolve) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        resolve({ width: img.naturalWidth, height: img.naturalHeight });
        URL.revokeObjectURL(url);
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        resolve({});
      };
      img.src = url;
    });

  const runAnalyze = async (imageId: string) => {
    setLoading(true, t('analyzing'));
    try {
      const res = await autoAnalyze(imageId, {
        chart_type_override: analyzeOptions.chart_type_override || undefined,
        use_vlm_regions: analyzeOptions.use_vlm_regions,
        force_redetect_plot: analyzeOptions.force_redetect_plot,
      });
      setAnalysis(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const applyUpload = async (
    upload: {
      image_id: string;
      url: string;
      source_type?: 'image' | 'pdf';
      source_id?: string;
      pages?: { page: number; width: number; height: number }[];
      selected_page?: number;
    },
    file: File,
    dims?: { width?: number; height?: number }
  ) => {
    setImage(upload.url, upload.image_id, {
      fileName: file.name,
      fileSize: file.size,
      mimeType: file.type || undefined,
      width: dims?.width,
      height: dims?.height,
    });
    setSourceMeta({
      sourceType: upload.source_type || 'image',
      sourceId: upload.source_id || upload.image_id,
      pdfPages: upload.pages || [],
      selectedPdfPage: upload.selected_page ?? 0,
    });
    await runAnalyze(upload.image_id);
  };

  const onFile = async (file: File) => {
    setLoading(true, t('uploading'));
    setError(null);
    setPendingPdfSelect(false);
    try {
      const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
      const dims = isPdf ? {} : await readDimensions(file);
      const upload = await uploadImage(file);
      if (upload.source_type === 'pdf' && (upload.pages?.length ?? 0) > 1) {
        setPendingPdfSelect(true);
        setSourceMeta({
          sourceType: 'pdf',
          sourceId: upload.source_id || null,
          pdfPages: upload.pages || [],
          selectedPdfPage: upload.selected_page ?? 0,
        });
        setImage(upload.url, upload.image_id, {
          fileName: file.name,
          fileSize: file.size,
          mimeType: file.type || 'application/pdf',
        });
        await runAnalyze(upload.image_id);
        return;
      }
      await applyUpload(upload, file, dims);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const onPdfPageChange = async (page: number) => {
    if (!sourceId) return;
    setLoading(true, t('uploading'));
    setError(null);
    try {
      const upload = await selectPdfPage(sourceId, page);
      setImage(upload.url, upload.image_id, {
        fileName: useStore.getState().imageInfo?.fileName,
        mimeType: 'application/pdf',
      });
      setSourceMeta({
        sourceType: 'pdf',
        sourceId: upload.source_id || sourceId,
        pdfPages: upload.pages || pdfPages,
        selectedPdfPage: page,
      });
      await runAnalyze(upload.image_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-panel center">
      <h2>{t('uploadTitle')}</h2>
      <p className="hint">{t('uploadHint')}</p>
      {sourceType === 'pdf' && pdfPages.length > 1 && (
        <label className="pdf-page-select">
          {t('pdfSelectPage')}
          <select
            value={selectedPdfPage}
            onChange={(e) => onPdfPageChange(Number(e.target.value))}
          >
            {pdfPages.map((p) => (
              <option key={p.page} value={p.page}>
                {t('pdfPageOption', { n: p.page + 1, w: p.width, h: p.height })}
              </option>
            ))}
          </select>
        </label>
      )}
      {pendingPdfSelect && pdfPages.length > 1 && (
        <p className="hint">{t('pdfMultiPageHint')}</p>
      )}
      <input
        ref={fileRef}
        type="file"
        accept="image/*,.pdf,application/pdf"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
      <button type="button" className="btn-primary" onClick={() => fileRef.current?.click()}>
        {t('chooseImage')}
      </button>
    </div>
  );
}
