import ReactECharts from 'echarts-for-react';
import { useT } from '../../i18n/useT';
import { useStore } from '../../store/useStore';

export const RebuiltChart: React.FC = () => {
  const { series, chartType, fitCurves } = useStore();
  const { t, locale } = useT();

  if (!series.length && !fitCurves.length) {
    return <div className="preview-empty">{t('rebuiltEmpty')}</div>;
  }

  const lineSeries = series.map((s) => ({
    name: s.name,
    type: chartType === 'scatter' ? 'scatter' : 'line',
    data: s.points.map((p) => [p.x, p.y]),
    itemStyle: { color: s.color_hex || undefined },
    showSymbol: true,
  }));

  const fitSeries = fitCurves.map((f, i) => ({
    name: (f.name as string) || `fit_${i}`,
    type: 'line',
    data: ((f.points as { x: number; y: number }[]) || []).map((p) => [p.x, p.y]),
    lineStyle: { type: 'dashed' as const },
    showSymbol: false,
  }));

  const option = {
    title: { text: t('rebuiltChart'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: [...series.map((s) => s.name), ...fitSeries.map((f) => f.name)] },
    xAxis: { type: 'value' },
    yAxis: { type: 'value' },
    series: [...lineSeries, ...fitSeries],
  };

  return (
    <ReactECharts
      key={locale}
      option={option}
      style={{ height: 280, width: '100%' }}
    />
  );
};
