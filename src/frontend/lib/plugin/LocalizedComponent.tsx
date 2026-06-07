import type { I18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { Skeleton } from '@mantine/core';
import { useEffect, useState } from 'react';

export type LocaleLoader = (locale: string) => Promise<any>;

async function tryLoadLocale(
  locale: string,
  loader: LocaleLoader
): Promise<any> {
  try {
    return await loader(locale);
  } catch (error) {
    console.warn(`Failed to load locale ${locale}`);
    return null;
  }
}

async function loadPluginLocale(
  i18n: I18n,
  locale: string,
  loader: LocaleLoader
) {
  let messages = null;

  messages = await tryLoadLocale(locale, loader);

  if (!messages && locale.includes('-')) {
    const fallbackLocale = locale.split('-')[0];
    console.debug(
      `Locale ${locale} not found, trying fallback locale ${fallbackLocale}`
    );
    messages = await tryLoadLocale(fallbackLocale, loader);
  }

  if (!messages && locale.includes('_')) {
    const fallbackLocale = locale.split('_')[0];
    console.debug(
      `Locale ${locale} not found, trying fallback locale ${fallbackLocale}`
    );
    messages = await tryLoadLocale(fallbackLocale, loader);
  }

  if (!messages && locale !== 'en') {
    console.debug(`Locale ${locale} not found, trying fallback locale en`);
    messages = await tryLoadLocale('en', loader);
  }

  if (messages?.messages) {
    i18n.load(locale, messages.messages);
    i18n.activate(locale);
  } else {
    console.error(`Failed to load any locale for ${locale}`);
  }
}

const defaultLocaleLoader: LocaleLoader = (locale) =>
  import(`./locales/${locale}/messages.ts`);

/**
 * Wrapper function for a plugin-defined component which needs to support dynamic locale loading.
 *
 * This is primarily designed for usage by the InvenTree plugin creator tool
 */
export default function LocalizedComponent({
  i18n,
  locale,
  loadLocale,
  children
}: {
  i18n: I18n;
  locale: string;
  loadLocale?: LocaleLoader;
  children: React.ReactNode;
}) {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setLoaded(false);
    loadPluginLocale(i18n, locale, loadLocale ?? defaultLocaleLoader).then(
      () => {
        setLoaded(true);
      }
    );
  }, [i18n, locale, loadLocale]);

  return loaded ? (
    <I18nProvider i18n={i18n}>{children}</I18nProvider>
  ) : (
    <Skeleton w='100%' animate />
  );
}
