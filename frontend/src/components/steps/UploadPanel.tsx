import { useRef } from 'react';
import { useT } from '../../i18n/useT';
import { uploadImage } from '../../services/api';
import { useStore } from '../../store/useStore';

export function UploadPanel() {
  const fileRef = useRef<HTMLInputElement>(null);
  const { setImage, setLoading, setError } = useStore();
  const { t } = useT();

  const onFile = async (file: File) => {
    setLoading(true, t('uploading'));
    setError(null);
    try {
      const { image_id, url } = await uploadImage(file);
      setImage(url, image_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-panel center">
      <h2>{t('uploadTitle')}</h2>
      <p className="hint">{t('uploadHint')}</p>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
      <button type="button" className="btn-primary" onClick={() => fileRef.current?.click()}>
        {t('chooseImage')}
      </button>
    </div>
  );
}
