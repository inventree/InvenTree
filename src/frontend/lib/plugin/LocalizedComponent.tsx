import type { I18n } from '@lingui/core';
import { I18nProvider } from '@lingui/react';
import { Skeleton } from '@mantine/core';
import { useEffect, useState } from 'react';

/*
 * To dynamically load locale messages from a plugin context,
 * the plugin MUST supply a callback function which can be used to load the locale messages for the plugin.
 * This is because the plugin frontend code is built separately from the main frontend,
 * and so cannot directly import locale messages from the main frontend.
 *
 * Refer to the inventree-plugin-creator tool for an example of how to use this component in a plugin context.
 */
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

/**
 * @param i18n - The i18n instance from the plugin context
 * @param locale - The current locale to load
 * @param loader - The callback function to load the locale messages for the plugin
 * @returns A React component which will load the locale messages and render the children once loaded
 */
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

// A default locale loader which can be used if the plugin does not supply its own loader function
// Note: This will return null, as the plugin is expected to supply its own loader function which can load the locale messages for the plugin
const defaultLocaleLoader: LocaleLoader = async (_locale: string) => null;

/**
 * Wrapper function for a plugin-defined component which needs to support dynamic locale loading.
 *
 * This is primarily designed for usage by the InvenTree plugin creator tool
 *
 * @param i18n - The i18n instance from the plugin context
 * @param locale - The current locale to load
 * @param loadLocale - The callback function to load the locale messages for the plugin
 * @param children - The child components to render once the locale is loaded
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
