import { i18n } from '@lingui/core';
import { Trans } from '@lingui/macro';
import { I18nProvider } from '@lingui/react';
import { useEffect } from 'react';

import { api } from '../App';
import { useLocalState } from '../states/LocalState';

// Definitions
export type Locales = keyof typeof languages | 'pseudo-LOCALE';

export const languages: Record<string, JSX.Element> = {
  cs: <Trans>Czech</Trans>,
  da: <Trans>Danish</Trans>,
  de: <Trans>German</Trans>,
  el: <Trans>Greek</Trans>,
  en: <Trans>English</Trans>,
  es: <Trans>Spanish</Trans>,
  'es-mx': <Trans>Spanish (Mexican)</Trans>,
  fa: <Trans>Farsi / Persian</Trans>,
  fi: <Trans>Finnish</Trans>,
  fr: <Trans>French</Trans>,
  he: <Trans>Hebrew</Trans>,
  hi: <Trans>Hindi</Trans>,
  hu: <Trans>Hungarian</Trans>,
  it: <Trans>Italian</Trans>,
  ja: <Trans>Japanese</Trans>,
  ko: <Trans>Korean</Trans>,
  nl: <Trans>Dutch</Trans>,
  no: <Trans>Norwegian</Trans>,
  pl: <Trans>Polish</Trans>,
  pt: <Trans>Portuguese</Trans>,
  'pt-br': <Trans>Portuguese (Brazilian)</Trans>,
  ru: <Trans>Russian</Trans>,
  sl: <Trans>Slovenian</Trans>,
  sv: <Trans>Swedish</Trans>,
  th: <Trans>Thai</Trans>,
  tr: <Trans>Turkish</Trans>,
  vi: <Trans>Vietnamese</Trans>,
  'zh-hans': <Trans>Chinese (Simplified)</Trans>,
  'zh-hant': <Trans>Chinese (Traditional)</Trans>
};

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
