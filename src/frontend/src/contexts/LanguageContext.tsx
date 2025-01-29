import { i18n } from '@lingui/core';
import { t } from '@lingui/macro';
import { I18nProvider } from '@lingui/react';
import { LoadingOverlay, Text } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';

import { api } from '../App';
import { useServerApiState } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { fetchGlobalStates } from '../states/states';

export const defaultLocale = 'en';

/*
 * Function which returns a record of supported languages.
 * Note that this is not a constant, as it is used in the LanguageSelect component
 */
export const getSupportedLanguages = (): Record<string, string> => {
  return {
    ar: t`Arabic`,
    bg: t`Bulgarian`,
    cs: t`Czech`,
    da: t`Danish`,
    de: t`German`,
    el: t`Greek`,
    en: t`English`,
    es: t`Spanish`,
    es_MX: t`Spanish (Mexican)`,
    et: t`Estonian`,
    fa: t`Farsi / Persian`,
    fi: t`Finnish`,
    fr: t`French`,
    he: t`Hebrew`,
    hi: t`Hindi`,
    hu: t`Hungarian`,
    it: t`Italian`,
    ja: t`Japanese`,
    ko: t`Korean`,
    lt: t`Lithuanian`,
    lv: t`Latvian`,
    nl: t`Dutch`,
    no: t`Norwegian`,
    pl: t`Polish`,
    pt: t`Portuguese`,
    pt_BR: t`Portuguese (Brazilian)`,
    ro: t`Romanian`,
    ru: t`Russian`,
    sk: t`Slovak`,
    sl: t`Slovenian`,
    sr: t`Serbian`,
    sv: t`Swedish`,
    th: t`Thai`,
    tr: t`Turkish`,
    uk: t`Ukrainian`,
    vi: t`Vietnamese`,
    zh_Hans: t`Chinese (Simplified)`,
    zh_Hant: t`Chinese (Traditional)`
  };
};

export function LanguageContext({
  children
}: Readonly<{ children: JSX.Element }>) {
  const [language] = useLocalState((state) => [state.language]);
  const [server] = useServerApiState((state) => [state.server]);

  useEffect(() => {
    activateLocale(defaultLocale);
  }, []);

  const [loadedState, setLoadedState] = useState<
    'loading' | 'loaded' | 'error'
  >('loading');
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;

    activateLocale(language)
      .then(() => {
        if (isMounted.current) setLoadedState('loaded');

        /*
         * Configure the default Accept-Language header for all requests.
         * - Locally selected locale
         * - Server default locale
         * - en-us (backup)
         */
        const locales: (string | undefined)[] = [];

        if (language != 'pseudo-LOCALE') {
          locales.push(language);
        }

        if (!!server.default_locale) {
          locales.push(server.default_locale);
        }

        if (locales.indexOf('en-us') < 0) {
          locales.push('en-us');
        }

        // Ensure that the locales are properly formatted
        const new_locales = locales
          .map((locale) => locale?.replaceAll('_', '-').toLowerCase())
          .join(', ');

        if (new_locales == api.defaults.headers.common['Accept-Language']) {
          return;
        }

        // Update default Accept-Language headers
        api.defaults.headers.common['Accept-Language'] = new_locales;

        // Reload server state (and refresh status codes)
        fetchGlobalStates();

        // Clear out cached table column names
        useLocalState.getState().clearTableColumnNames();
      })
      /* istanbul ignore next */
      .catch((err) => {
        console.error('ERR: Failed loading translations', err);
        if (isMounted.current) setLoadedState('error');
      });

    return () => {
      isMounted.current = false;
    };
  }, [language]);

  if (loadedState === 'loading') {
    return <LoadingOverlay visible={true} />;
  }

  /* istanbul ignore next */
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

export async function activateLocale(locale: string) {
  const { messages } = await import(`../locales/${locale}/messages.ts`);
  i18n.load(locale, messages);
  i18n.activate(locale);
}
