import { useT } from '../i18n/useT';
import { useStore } from '../store/useStore';

export function AnalysisInfoPanel() {
  const {
    chartType,
    chartMetadata,
    semantics,
    suggestedTicks,
    axisConfidence,
    regions,
    analysisSnapshot,
  } = useStore();
  const { t } = useT();

  const meta = chartMetadata;
  const xt = (suggestedTicks?.x_ticks as Array<{ pixel: number; value: number }>) || [];
  const yt = (suggestedTicks?.y_ticks as Array<{ pixel: number; value: number }>) || [];
  const plotArea = regions?.regions?.find((r) => r.kind === 'plot_area');
  const ocrSummary = analysisSnapshot?.ocr_summary as string[] | undefined;

  return (
    <section className="analysis-info-panel">
      <h3>{t('analysisInfoTitle')}</h3>
      <dl className="metadata-summary analysis-info-dl">
        <dt>{t('chartType')}</dt>
        <dd>{chartType}</dd>
        {meta?.title && (
          <>
            <dt>{t('metaTitle')}</dt>
            <dd>{meta.title}</dd>
          </>
        )}
        {(meta?.x_quantity || meta?.x_label) && (
          <>
            <dt>{t('metaXAxis')}</dt>
            <dd>
              {meta.x_quantity || meta.x_label}
              {meta.x_unit ? ` (${meta.x_unit})` : ''}
              {(chartMetadata as { x_scale?: string })?.x_scale || semantics?.x_scale
                ? ` · ${(chartMetadata as { x_scale?: string })?.x_scale || semantics?.x_scale}`
                : ''}
            </dd>
          </>
        )}
        {(meta?.y_quantity || meta?.y_label) && (
          <>
            <dt>{t('metaYAxis')}</dt>
            <dd>
              {meta.y_quantity || meta.y_label}
              {meta.y_unit ? ` (${meta.y_unit})` : ''}
              {(chartMetadata as { y_scale?: string })?.y_scale || semantics?.y_scale
                ? ` · ${(chartMetadata as { y_scale?: string })?.y_scale || semantics?.y_scale}`
                : ''}
            </dd>
          </>
        )}
        {meta?.legend && meta.legend.length > 0 && (
          <>
            <dt>{t('metaLegend')}</dt>
            <dd>{meta.legend.join(' · ')}</dd>
          </>
        )}
        {plotArea && (
          <>
            <dt>{t('plotAreaSource')}</dt>
            <dd>
              {plotArea.source || 'unknown'} · [{plotArea.bbox.x0}, {plotArea.bbox.y0}] – [
              {plotArea.bbox.x1}, {plotArea.bbox.y1}]
            </dd>
          </>
        )}
        {axisConfidence && (
          <>
            <dt>{t('axisConfidenceLabel')}</dt>
            <dd>
              X {(Math.round((axisConfidence.x_axis ?? 0) * 100))}% · Y{' '}
              {(Math.round((axisConfidence.y_axis ?? 0) * 100))}% · plot{' '}
              {(Math.round((axisConfidence.plot_area ?? 0) * 100))}%
            </dd>
          </>
        )}
        {xt.length > 0 && (
          <>
            <dt>{t('xTicksDetected')}</dt>
            <dd>{xt.map((t) => t.value).join(', ')}</dd>
          </>
        )}
        {yt.length > 0 && (
          <>
            <dt>{t('yTicksDetected')}</dt>
            <dd>{yt.map((t) => t.value).join(', ')}</dd>
          </>
        )}
        {ocrSummary && ocrSummary.length > 0 && (
          <>
            <dt>{t('ocrLabels')}</dt>
            <dd className="ocr-summary">{ocrSummary.slice(0, 24).join(' · ')}</dd>
          </>
        )}
        {regions?.regions && (
          <>
            <dt>{t('regionKinds')}</dt>
            <dd>
              {[...new Set(regions.regions.map((r) => r.kind))].join(', ')} ({regions.regions.length})
            </dd>
          </>
        )}
      </dl>
    </section>
  );
}
