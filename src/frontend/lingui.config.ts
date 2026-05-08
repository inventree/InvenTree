import { defineConfig } from '@lingui/cli';
import { formatter } from '@lingui/format-po';

export default defineConfig({
  locales: [
    'ar',
    'bg',
    'cs',
    'da',
    'de',
    'el',
    'en',
    'es',
    'es_MX',
    'et',
    'fa',
    'fi',
    'fr',
    'he',
    'hi',
    'hu',
    'it',
    'ja',
    'ko',
    'lt',
    'lv',
    'nl',
    'no',
    'pl',
    'pt',
    'pt_BR',
    'ro',
    'ru',
    'sk',
    'sl',
    'sr',
    'sv',
    'th',
    'tr',
    'uk',
    'vi',
    'zh_Hans',
    'zh_Hant',
    'pseudo-LOCALE'
  ],
  format: formatter({ lineNumbers: true }),
  sourceLocale: 'en',
  pseudoLocale: 'pseudo-LOCALE',
  orderBy: 'origin',
  fallbackLocales: {
    default: 'en',
    'pseudo-LOCALE': 'en'
  },
  catalogs: [
    {
      path: 'src/locales/{locale}/messages',
      include: ['src', 'lib'],
      exclude: ['**/node_modules/**', './dist/**']
    }
  ]
});
