import { useCallback } from 'react';
import { type TranslationKey, t as translate } from './translations';
import { useStore } from '../store/useStore';

export function useT() {
  const locale = useStore((s) => s.locale);
  const fn = useCallback(
    (key: TranslationKey, vars?: Record<string, string | number>) =>
      translate(locale, key, vars),
    [locale]
  );
  return { t: fn, locale };
}
