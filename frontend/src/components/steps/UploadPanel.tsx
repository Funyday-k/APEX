import { useRef } from 'react';
import { uploadImage } from '../../services/api';
import { useStore } from '../../store/useStore';

export function UploadPanel() {
  const fileRef = useRef<HTMLInputElement>(null);
  const { setImage, setLoading, setError } = useStore();

  const onFile = async (file: File) => {
    setLoading(true, '上传中…');
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
      <h2>上传科研图表</h2>
      <p className="hint">支持 PNG / JPG / WebP 等常见格式</p>
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
        选择图片
      </button>
    </div>
  );
}
