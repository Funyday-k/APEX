import ReactECharts from 'echarts-for-react';
import { useT } from '../../i18n/useT';
import { useStore } from '../../store/useStore';

type Props = { height?: number };

export const RebuiltChart: React.FC<Props> = ({ height = 360 }) => {
  const { series, chartType, fitCurves, xScale, yScale, showFitCurves } = useStore();
  const { t, locale } = useT();

  if (!series.length && (!showFitCurves || !fitCurves.length)) {
    return <div className="preview-empty">{t('rebuiltEmpty')}</div>;
  }

  const boxCategories: string[] = [];
  const mainSeries = series.map((s) => {
    const sorted = [...s.points].sort((a, b) => a.x - b.x);

    if (chartType === 'bar') {
      return {
        name: s.name,
        type: 'bar' as const,
        data: sorted.map((p) => p.y),
        itemStyle: { color: s.color_hex || undefined },
      };
    }

    if (chartType === 'box') {
      const boxes = [];
      for (let i = 0; i + 4 < sorted.length; i += 5) {
        const group = sorted.slice(i, i + 5);
        boxCategories.push(String(group[0].x));
        boxes.push(group.map((p) => p.y));
      }
      return {
        name: s.name,
        type: 'boxplot' as const,
        data: boxes,
        itemStyle: { color: s.color_hex || undefined },
      };
    }

    return {
      name: s.name,
      type: (chartType === 'scatter' || chartType === 'heatmap' ? 'scatter' : 'line') as
        | 'scatter'
        | 'line',
      data: sorted.map((p) => [p.x, p.y]),
      itemStyle: { color: s.color_hex || undefined },
      showSymbol: true,
    };
  });

  const fitSeries = showFitCurves
    ? fitCurves.map((f, i) => ({
        name: (f.name as string) || `fit_${i}`,
        type: 'line' as const,
        data: ((f.points as { x: number; y: number }[]) || [])
          .sort((a, b) => a.x - b.x)
          .map((p) => [p.x, p.y]),
        lineStyle: { type: 'dashed' as const },
        showSymbol: false,
      }))
    : [];

  const valueAxis = (scale: 'linear' | 'log') =>
    scale === 'log' ? { type: 'log' as const } : { type: 'value' as const };

  const option = {
    title: { text: t('rebuiltChart'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: chartType === 'box' ? 'item' : 'axis' },
    legend: { data: [...series.map((s) => s.name), ...fitSeries.map((f) => f.name)] },
    xAxis:
      chartType === 'box'
        ? { type: 'category' as const, data: boxCategories }
        : valueAxis(xScale),
    yAxis: valueAxis(yScale),
    series: [...mainSeries, ...fitSeries],
  };

  return (
    <ReactECharts
      key={`${locale}-${xScale}-${yScale}`}
      option={option}
      style={{ height, width: '100%' }}
    />
  );
};
