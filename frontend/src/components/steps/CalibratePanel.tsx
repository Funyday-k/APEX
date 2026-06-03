import { ImageCanvas } from '../Canvas/ImageCanvas';
import { useStore } from '../../store/useStore';

export function CalibratePanel() {
  const {
    chartType,
    setChartType,
    xRefs,
    yRefs,
    xScale,
    yScale,
    calibAxis,
    setCalibAxis,
    setScale,
    clearCalib,
    setStep,
  } = useStore();

  return (
    <div className="step-panel split">
      <div className="side-controls">
        <h2>坐标标定</h2>
        <label>
          图表类型
          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value as typeof chartType)}
          >
            <option value="line">折线图</option>
            <option value="scatter">散点图</option>
            <option value="bar">柱状图</option>
            <option value="heatmap">热图</option>
            <option value="box">箱线图</option>
          </select>
        </label>
        <label>
          当前轴
          <select value={calibAxis} onChange={(e) => setCalibAxis(e.target.value as 'x' | 'y')}>
            <option value="x">X 轴（2 点）</option>
            <option value="y">Y 轴（2 点）</option>
          </select>
        </label>
        <label>
          X 轴刻度
          <select value={xScale} onChange={(e) => setScale('x', e.target.value as 'linear' | 'log')}>
            <option value="linear">线性</option>
            <option value="log">对数</option>
          </select>
        </label>
        <label>
          Y 轴刻度
          <select value={yScale} onChange={(e) => setScale('y', e.target.value as 'linear' | 'log')}>
            <option value="linear">线性</option>
            <option value="log">对数</option>
          </select>
        </label>
        <p className="hint">
          在图上点击设置参考点并输入数值。X: {xRefs.length}/2 · Y: {yRefs.length}/2
        </p>
        <div className="btn-row">
          <button type="button" className="btn-muted" onClick={clearCalib}>
            清除标定
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={xRefs.length < 2 || yRefs.length < 2}
            onClick={() => setStep('extract')}
          >
            下一步：提取
          </button>
        </div>
      </div>
      <div className="canvas-wrap">
        <ImageCanvas mode="calibrating" />
      </div>
    </div>
  );
}
