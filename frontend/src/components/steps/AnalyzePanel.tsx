import useImage from 'use-image';
import { useT } from '../../i18n/useT';
import { autoAnalyze, selectPdfPage } from '../../services/api';
import { AdvancedOptionsPanel } from '../AdvancedOptionsPanel';
import { ImageCanvas } from '../Canvas/ImageCanvas';
import { RegionAdjustModal } from '../Canvas/RegionAdjustModal';
import { StepNav } from '../StepNav';
import { REGION_KINDS } from '../../utils/regions';
import { useStore } from '../../store/useStore';
import { CasesPanel } from './CasesPanel';

export function AnalyzePanel() {
  const {
    imageId,
    imageUrl,
    analysisDone,
    regionsConfirmed,
    setAnalysis,
    setLoading,
    setError,
    setStep,
    setImage,
    setSourceMeta,
    analyzeOptions,
    autoCalibConfidence,
    autoCalibPending,
    applySuggestedCalibration,
    confirmRegions,
    regions,
    sourceType,
    sourceId,
    pdfPages,
    selectedPdfPage,
    selectedRegionIndex,
    newRegionKind,
    setNewRegionKind,
    addRegion,
    deleteRegion,
    setRegionKind,
    updateRegion,
    regionAdjustOpen,
    setRegionAdjustOpen,
    imageGeometry,
  } = useStore();
  const { t } = useT();
  const [image] = useImage(imageUrl || '', 'anonymous');

  const run = async () => {
    if (!imageId) return;
    setLoading(true, t('analyzing'));
    setError(null);
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

  const onPdfPageChange = async (page: number) => {
    if (!sourceId) return;
    setLoading(true, t('analyzing'));
    setError(null);
    try {
      const upload = await selectPdfPage(sourceId, page);
      setImage(upload.url, upload.image_id);
      setSourceMeta({
        sourceType: 'pdf',
        sourceId: upload.source_id || sourceId,
        pdfPages: upload.pages || pdfPages,
        selectedPdfPage: page,
      });
      const res = await autoAnalyze(upload.image_id, {
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

  const confirmAndCalibrate = () => {
    confirmRegions();
    setStep('calibrate');
  };

  if (!imageUrl) return null;

  const regionCount = regions?.regions?.length ?? 0;

  return (
    <div className="step-panel split analyze-panel">
      <div className="side-controls">
        <h2>{t('analyzeTitle')}</h2>
        <p className="hint">{t('analyzeHint')}</p>
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
        {analysisDone && regionCount > 0 && (
          <p className="hint">
            {regionsConfirmed ? t('regionsConfirmed') : t('regionsPending', { n: regionCount })}
          </p>
        )}
        {analysisDone && (
          <div className="region-edit-tools">
            <p className="hint">{t('regionEditHint')}</p>
            <label>
              {t('regionKind')}
              <select value={newRegionKind} onChange={(e) => setNewRegionKind(e.target.value)}>
                {REGION_KINDS.map((k) => (
                  <option key={k} value={k}>
                    {k}
                  </option>
                ))}
              </select>
            </label>
            <div className="btn-row">
              <button type="button" className="btn-muted" onClick={() => addRegion(newRegionKind)}>
                {t('addRegion')}
              </button>
              <button
                type="button"
                className="btn-muted"
                disabled={selectedRegionIndex == null}
                onClick={() =>
                  selectedRegionIndex != null && deleteRegion(selectedRegionIndex)
                }
              >
                {t('deleteRegion')}
              </button>
            </div>
            {selectedRegionIndex != null && regions?.regions[selectedRegionIndex] && (
              <label>
                {t('regionKindSelected')}
                <select
                  value={regions.regions[selectedRegionIndex].kind}
                  onChange={(e) => setRegionKind(selectedRegionIndex, e.target.value)}
                >
                  {REGION_KINDS.map((k) => (
                    <option key={k} value={k}>
                      {k}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {selectedRegionIndex != null && (
              <button
                type="button"
                className="btn-muted"
                onClick={() => setRegionAdjustOpen(true)}
              >
                {t('regionFineTune')}
              </button>
            )}
          </div>
        )}
        {analysisDone && <CasesPanel />}
        <AdvancedOptionsPanel mode="analyze" />
        <div className="btn-row">
          <button type="button" className="btn-muted" onClick={run}>
            {analysisDone ? t('reAnalyze') : t('startAnalyze')}
          </button>
          <StepNav backTo="upload" />
          {analysisDone && (
            <button type="button" className="btn-primary" onClick={confirmAndCalibrate}>
              {t('confirmRegions')}
            </button>
          )}
          {!analysisDone && (
            <button type="button" className="btn-muted" onClick={() => setStep('calibrate')}>
              {t('skipToCalibrate')}
            </button>
          )}
        </div>
        {analysisDone && (
          <div className="analyze-results">
            {autoCalibConfidence > 0 && (
              <p className="hint">
                {autoCalibPending
                  ? t('autoCalibPending', { pct: Math.round(autoCalibConfidence * 100) })
                  : t('autoCalibApplied', { pct: Math.round(autoCalibConfidence * 100) })}
              </p>
            )}
            {autoCalibPending && (
              <button type="button" className="btn-muted" onClick={applySuggestedCalibration}>
                {t('applyAiAxisCalibration')}
              </button>
            )}
          </div>
        )}
      </div>
      <div className="canvas-wrap canvas-wrap-viewport">
        <ImageCanvas mode="preview" />
      </div>
      {regionAdjustOpen &&
        image &&
        imageGeometry &&
        selectedRegionIndex != null &&
        regions?.regions[selectedRegionIndex] && (
          <RegionAdjustModal
            open
            image={image}
            geometry={imageGeometry}
            bbox={regions.regions[selectedRegionIndex].bbox}
            onBBoxChange={(bbox) => updateRegion(selectedRegionIndex, bbox)}
            onClose={() => setRegionAdjustOpen(false)}
          />
        )}
    </div>
  );
}
