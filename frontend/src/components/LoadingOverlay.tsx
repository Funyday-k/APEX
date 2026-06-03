import { useT } from '../i18n/useT';
import { useStore } from '../store/useStore';

export function LoadingOverlay() {
  const { loading, loadingMsg } = useStore();
  const { t } = useT();
  if (!loading) return null;
  return <div className="loading-overlay">{loadingMsg || t('loadingDefault')}</div>;
}
