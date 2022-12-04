import { i18n } from '@lingui/core';
import { de, en, hu } from "make-plural/plurals";
import { api } from './App';

// Definitions
export type Locales = 'en' | 'de' | 'hu' | 'pseudo-LOCALE';
export const languages: Locales[] = ['en', 'de', 'hu'];

// Functions
export function loadLocales() {
    i18n.loadLocaleData({
        de: { plurals: de },
        en: { plurals: en },
        hu: { plurals: hu },
    });
}

export async function activateLocale(locale: Locales) {
    const { messages } = await import(`./locales/${locale}/messages.ts`)
    i18n.load(locale, messages)
    i18n.activate(locale)

    // Set api header
    api.defaults.headers.common['Accept-Language'] = locale;
}
