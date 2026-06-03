import { useStore } from '../store/useStore';

export function LoadingOverlay() {
  const { loading, loadingMsg } = useStore();
  if (!loading) return null;
  return <div className="loading-overlay">{loadingMsg || '处理中…'}</div>;
}
