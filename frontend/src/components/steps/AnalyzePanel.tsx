import { autoAnalyze } from '../../services/api';
import { useStore } from '../../store/useStore';

export function AnalyzePanel() {
  const { imageId, imageUrl, setAnalysis, setLoading, setError, setStep } = useStore();

  const run = async () => {
    if (!imageId) return;
    setLoading(true, '自动分析中…');
    setError(null);
    try {
      const res = await autoAnalyze(imageId);
      setAnalysis(res.chart_type, res.suggested_calibration, res.semantics);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-panel">
      <h2>自动分析</h2>
      {imageUrl && (
        <img src={imageUrl} alt="preview" className="preview-thumb" />
      )}
      <p className="hint">识别图类型、OCR 刻度与 VLM 语义（若已配置 API Key）</p>
      <div className="btn-row">
        <button type="button" className="btn-primary" onClick={run}>
          开始分析
        </button>
        <button type="button" className="btn-muted" onClick={() => setStep('calibrate')}>
          跳过，手动标定
        </button>
      </div>
    </div>
  );
}
