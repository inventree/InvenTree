import { i18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { useEffect } from 'react';

import { api } from '../App';
import { useLocalState } from '../states/LocalState';

// Definitions
export type Locales = 'en' | 'de' | 'hu' | 'pseudo-LOCALE';
export const languages: Locales[] = ['en', 'de', 'hu'];

export function LanguageContext({ children }: { children: JSX.Element }) {
  const [language] = useLocalState((state) => [state.language]);

  useEffect(() => {
    activateLocale(language);
  }, [language]);

  return <I18nProvider i18n={i18n}>{children}</I18nProvider>;
}

export async function activateLocale(locale: Locales) {
  const { messages } = await import(`../locales/${locale}/messages.ts`);
  i18n.load(locale, messages);
  i18n.activate(locale);

  // Set api header
  api.defaults.headers.common['Accept-Language'] = locale;
}
