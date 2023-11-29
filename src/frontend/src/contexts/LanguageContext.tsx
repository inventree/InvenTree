import { i18n } from '@lingui/core';
import { t } from '@lingui/macro';
import { I18nProvider } from '@lingui/react';
import { LoadingOverlay, Text } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';

import { api } from '../App';
import { useLocalState } from '../states/LocalState';

// Definitions
export type Locales = keyof typeof languages | 'pseudo-LOCALE';

export const languages: Record<string, string> = {
  bg: t`Bulgarian`,
  cs: t`Czech`,
  da: t`Danish`,
  de: t`German`,
  el: t`Greek`,
  en: t`English`,
  es: t`Spanish`,
  'es-mx': t`Spanish (Mexican)`,
  fa: t`Farsi / Persian`,
  fi: t`Finnish`,
  fr: t`French`,
  he: t`Hebrew`,
  hi: t`Hindi`,
  hu: t`Hungarian`,
  it: t`Italian`,
  ja: t`Japanese`,
  ko: t`Korean`,
  nl: t`Dutch`,
  no: t`Norwegian`,
  pl: t`Polish`,
  pt: t`Portuguese`,
  'pt-br': t`Portuguese (Brazilian)`,
  ru: t`Russian`,
  sl: t`Slovenian`,
  sv: t`Swedish`,
  th: t`Thai`,
  tr: t`Turkish`,
  vi: t`Vietnamese`,
  'zh-hans': t`Chinese (Simplified)`,
  'zh-hant': t`Chinese (Traditional)`
};

export function LanguageContext({ children }: { children: JSX.Element }) {
  const [language] = useLocalState((state) => [state.language]);

  const [loadedState, setLoadedState] = useState<
    'loading' | 'loaded' | 'error'
  >('loading');
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;

    activateLocale(language)
      .then(() => {
        if (isMounted.current) setLoadedState('loaded');
      })
      .catch((err) => {
        console.error('Failed loading translations', err);
        if (isMounted.current) setLoadedState('error');
      });

    return () => {
      isMounted.current = false;
    };
  }, [language]);

  if (loadedState === 'loading') {
    return <LoadingOverlay visible={true} />;
  }

  if (loadedState === 'error') {
    return (
      <Text>
        An error occurred while loading translations, see browser console for
        details.
      </Text>
    );
  }

  // only render the i18n Provider if the locales are fully activated, otherwise we end
  // up with an error in the browser console
  return <I18nProvider i18n={i18n}>{children}</I18nProvider>;
}

export async function activateLocale(locale: Locales) {
  const { messages } = await import(`../locales/${locale}/messages.ts`);
  i18n.load(locale, messages);
  i18n.activate(locale);

  // Set api header
  api.defaults.headers.common['Accept-Language'] = locale;
}
