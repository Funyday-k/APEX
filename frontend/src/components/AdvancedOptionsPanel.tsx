import { useT } from '../i18n/useT';
import { useStore } from '../store/useStore';

type Props = {
  mode: 'analyze' | 'extract';
};

export function AdvancedOptionsPanel({ mode }: Props) {
  const { analyzeOptions, extractOptions, setAnalyzeOptions, setExtractOptions, chartType, setChartType } =
    useStore();
  const { t } = useT();

  return (
    <details className="advanced-options">
      <summary>{t('advancedOptions')}</summary>
      {mode === 'analyze' ? (
        <div className="advanced-options-body">
          <label>
            {t('chartTypeOverride')}
            <select
              value={analyzeOptions.chart_type_override}
              onChange={(e) => setAnalyzeOptions({ chart_type_override: e.target.value })}
            >
              <option value="">{t('chartTypeAuto')}</option>
              <option value="line">{t('chartLine')}</option>
              <option value="scatter">{t('chartScatter')}</option>
              <option value="bar">{t('chartBar')}</option>
              <option value="heatmap">{t('chartHeatmap')}</option>
              <option value="box">{t('chartBox')}</option>
            </select>
          </label>
          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={analyzeOptions.use_vlm_regions}
              onChange={(e) => setAnalyzeOptions({ use_vlm_regions: e.target.checked })}
            />
            {t('useVlmRegions')}
          </label>
          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={analyzeOptions.force_redetect_plot}
              onChange={(e) => setAnalyzeOptions({ force_redetect_plot: e.target.checked })}
            />
            {t('forceRedetectPlot')}
          </label>
        </div>
      ) : (
        <div className="advanced-options-body">
          <label>
            {t('chartType')}
            <select value={chartType} onChange={(e) => setChartType(e.target.value as typeof chartType)}>
              <option value="line">{t('chartLine')}</option>
              <option value="scatter">{t('chartScatter')}</option>
              <option value="bar">{t('chartBar')}</option>
              <option value="heatmap">{t('chartHeatmap')}</option>
              <option value="box">{t('chartBox')}</option>
            </select>
          </label>
          <label>
            {t('colorTolerance')}
            <input
              type="number"
              min={1}
              max={80}
              value={extractOptions.color_tolerance}
              onChange={(e) =>
                setExtractOptions({ color_tolerance: Number(e.target.value) || 30 })
              }
            />
          </label>
          <label>
            {t('minMarkerArea')}
            <input
              type="number"
              min={1}
              max={500}
              value={extractOptions.min_marker_area}
              onChange={(e) =>
                setExtractOptions({ min_marker_area: Number(e.target.value) || 8 })
              }
            />
          </label>
          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={extractOptions.suppress_grid}
              onChange={(e) => setExtractOptions({ suppress_grid: e.target.checked })}
            />
            {t('suppressGrid')}
          </label>
          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={extractOptions.intersect_auto}
              onChange={(e) => setExtractOptions({ intersect_auto: e.target.checked })}
            />
            {t('intersectAuto')}
          </label>
          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={extractOptions.enable_vlm_audit}
              onChange={(e) => setExtractOptions({ enable_vlm_audit: e.target.checked })}
            />
            {t('enableVlmAudit')}
          </label>
          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={extractOptions.enable_ai_evaluation}
              onChange={(e) => setExtractOptions({ enable_ai_evaluation: e.target.checked })}
            />
            {t('enableAiEvaluation')}
          </label>
        </div>
      )}
    </details>
  );
}
