import ReactECharts from 'echarts-for-react';
import { useT } from '../../i18n/useT';
import { useStore } from '../../store/useStore';
import { latexToPlain } from '../../utils/latex';
import { LatexText } from '../LatexText';

type Props = { height?: number };

type ErrorBarEntry = {
  y_err_upper?: number | null;
  y_err_lower?: number | null;
  x_err_left?: number | null;
  x_err_right?: number | null;
};

type ErrorBand = {
  name?: string;
  color_hex?: string;
  upper_points?: { x: number; y: number }[];
  lower_points?: { x: number; y: number }[];
};

export const RebuiltChart: React.FC<Props> = ({ height = 360 }) => {
  const {
    series,
    chartType,
    fitCurves,
    errorBands,
    xScale,
    yScale,
    showFitCurves,
    chartMetadata,
  } = useStore();
  const { t, locale } = useT();

  if (!series.length && (!showFitCurves || !fitCurves.length)) {
    return <div className="preview-empty">{t('rebuiltEmpty')}</div>;
  }

  const titleText =
    chartMetadata?.title || chartMetadata?.x_quantity
      ? latexToPlain(chartMetadata?.title) || t('rebuiltChart')
      : t('rebuiltChart');
  const xName = latexToPlain(
    chartMetadata?.x_label ||
      [chartMetadata?.x_quantity, chartMetadata?.x_unit && `(${chartMetadata.x_unit})`]
        .filter(Boolean)
        .join(' ')
  );
  const yName = latexToPlain(
    chartMetadata?.y_label ||
      [chartMetadata?.y_quantity, chartMetadata?.y_unit && `(${chartMetadata.y_unit})`]
        .filter(Boolean)
        .join(' ')
  );

  const boxCategories: string[] = [];
  const mainSeries = series.flatMap((s) => {
    const sorted = [...s.points].sort((a, b) => a.x - b.x);
    const out: Record<string, unknown>[] = [];

    const band = s.error_band as ErrorBand | undefined;
    if (band?.upper_points?.length && band?.lower_points?.length) {
      const upper = [...band.upper_points].sort((a, b) => a.x - b.x);
      const lower = [...band.lower_points].sort((a, b) => a.x - b.x);
      const poly = [
        ...upper.map((p) => [p.x, p.y]),
        ...[...lower].reverse().map((p) => [p.x, p.y]),
      ];
      out.push({
        name: `${s.name} band`,
        type: 'line',
        data: poly,
        lineStyle: { width: 0 },
        areaStyle: { color: (s.color_hex || '#888') + '33' },
        showSymbol: false,
        tooltip: { show: false },
        z: 1,
      });
    }

    if (chartType === 'bar') {
      out.push({
        name: s.name,
        type: 'bar' as const,
        data: sorted.map((p) => p.y),
        itemStyle: { color: s.color_hex || undefined },
      });
      return out;
    }

    if (chartType === 'box') {
      const boxes = [];
      for (let i = 0; i + 4 < sorted.length; i += 5) {
        const group = sorted.slice(i, i + 5);
        boxCategories.push(String(group[0].x));
        boxes.push(group.map((p) => p.y));
      }
      out.push({
        name: s.name,
        type: 'boxplot' as const,
        data: boxes,
        itemStyle: { color: s.color_hex || undefined },
      });
      return out;
    }

    const isScatter =
      chartType === 'scatter' ||
      chartType === 'heatmap' ||
      s.representation === 'markers' ||
      s.representation === 'marker_line';
    const showSymbol = isScatter || s.representation === 'marker_line';

    out.push({
      name: s.name,
      type: (isScatter ? 'scatter' : 'line') as 'scatter' | 'line',
      data: sorted.map((p) => [p.x, p.y]),
      itemStyle: { color: s.color_hex || undefined },
      showSymbol,
      symbolSize: showSymbol ? 6 : 4,
      lineStyle: { width: s.representation === 'markers' ? 0 : 2 },
      z: 3,
    });

    if (s.has_error_bars && s.errors?.length) {
      const errData = sorted.map((p, i) => {
        const e = (s.errors?.[i] || {}) as ErrorBarEntry;
        return [
          p.x,
          p.y,
          e.y_err_lower ?? e.y_err_upper ?? 0,
          e.y_err_upper ?? e.y_err_lower ?? 0,
        ];
      });
      out.push({
        name: `${s.name} ±`,
        type: 'custom',
        renderItem: (_params: unknown, api: { value: (i: number) => number; coord: (v: number[]) => number[]; style: (o: object) => object; visual: (k: string) => string }) => {
          const x = api.value(0);
          const y = api.value(1);
          const low = api.value(2);
          const high = api.value(3);
          const pt = api.coord([x, y]);
          const top = api.coord([x, y + high]);
          const bot = api.coord([x, y - low]);
          return {
            type: 'group',
            children: [
              {
                type: 'line',
                shape: { x1: pt[0], y1: top[1], x2: pt[0], y2: bot[1] },
                style: api.style({ stroke: api.visual('color'), lineWidth: 1.5 }),
              },
              {
                type: 'line',
                shape: { x1: pt[0] - 4, y1: top[1], x2: pt[0] + 4, y2: top[1] },
                style: api.style({ stroke: api.visual('color'), lineWidth: 1.5 }),
              },
              {
                type: 'line',
                shape: { x1: pt[0] - 4, y1: bot[1], x2: pt[0] + 4, y2: bot[1] },
                style: api.style({ stroke: api.visual('color'), lineWidth: 1.5 }),
              },
            ],
          };
        },
        encode: { x: 0, y: 1 },
        data: errData,
        z: 4,
        tooltip: { show: false },
      });
    }

    return out;
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

  const legendNames = [
    ...series.map((s) => s.name),
    ...(chartMetadata?.legend?.length ? chartMetadata.legend : []),
    ...fitSeries.map((f) => f.name),
  ];
  const uniqueLegend = [...new Set(legendNames)];

  const option = {
    title: { show: false },
    tooltip: { trigger: chartType === 'box' ? 'item' : 'axis' },
    legend: { data: uniqueLegend, top: 8 },
    grid: { top: 72, left: 64, right: 24, bottom: 48 },
    xAxis:
      chartType === 'box'
        ? { type: 'category' as const, data: boxCategories, name: xName, nameLocation: 'middle', nameGap: 28 }
        : { ...valueAxis(xScale), name: xName, nameLocation: 'middle', nameGap: 28 },
    yAxis: { ...valueAxis(yScale), name: yName, nameLocation: 'middle', nameGap: 48 },
    series: [...mainSeries, ...fitSeries],
  };

  return (
    <div className="rebuilt-chart-wrap">
      <div className="rebuilt-chart-header">
        <LatexText text={chartMetadata?.title || titleText} as="div" className="rebuilt-title" displayMode />
        {(chartMetadata?.x_label || chartMetadata?.y_label) && (
          <div className="rebuilt-axis-labels hint">
            <LatexText text={chartMetadata?.x_label || xName} /> ·{' '}
            <LatexText text={chartMetadata?.y_label || yName} />
          </div>
        )}
      </div>
      <ReactECharts
        key={`${locale}-${xScale}-${yScale}-${series.length}`}
        option={option}
        style={{ height, width: '100%' }}
      />
    </div>
  );
};
