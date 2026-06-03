import { useStore } from '../store/useStore';
import { useT } from '../i18n/useT';

export function LanguageSwitcher() {
  const { locale, setLocale } = useStore();
  const { t } = useT();

  return (
    <div className="lang-switcher" role="group" aria-label="Language">
      <button
        type="button"
        className={locale === 'zh' ? 'active' : ''}
        onClick={() => setLocale('zh')}
      >
        {t('langZh')}
      </button>
      <button
        type="button"
        className={locale === 'en' ? 'active' : ''}
        onClick={() => setLocale('en')}
      >
        {t('langEn')}
      </button>
    </div>
  );
}
