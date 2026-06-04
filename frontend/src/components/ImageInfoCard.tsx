import { useT } from '../i18n/useT';
import type { ImageInfo } from '../store/useStore';

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

type Props = {
  info: ImageInfo | null;
  compact?: boolean;
};

export function ImageInfoCard({ info, compact }: Props) {
  const { t } = useT();
  if (!info) return null;

  const dim =
    info.width && info.height ? `${info.width} × ${info.height} px` : t('imageInfoDimPending');

  return (
    <section className={`image-info-card${compact ? ' compact' : ''}`}>
      <h3 className="image-info-title">{t('imageInfoTitle')}</h3>
      <dl className="metadata-summary image-info-dl">
        {info.fileName && (
          <>
            <dt>{t('imageInfoFileName')}</dt>
            <dd title={info.fileName}>{info.fileName}</dd>
          </>
        )}
        <dt>{t('imageInfoDimensions')}</dt>
        <dd>{dim}</dd>
        {info.fileSize != null && (
          <>
            <dt>{t('imageInfoFileSize')}</dt>
            <dd>{formatBytes(info.fileSize)}</dd>
          </>
        )}
        {info.mimeType && (
          <>
            <dt>{t('imageInfoMime')}</dt>
            <dd>{info.mimeType}</dd>
          </>
        )}
        {info.imageId && !compact && (
          <>
            <dt>{t('imageInfoId')}</dt>
            <dd className="mono truncate">{info.imageId}</dd>
          </>
        )}
        {info.regionCount != null && info.regionCount > 0 && (
          <>
            <dt>{t('imageInfoRegions')}</dt>
            <dd>{info.regionCount}</dd>
          </>
        )}
      </dl>
    </section>
  );
}
