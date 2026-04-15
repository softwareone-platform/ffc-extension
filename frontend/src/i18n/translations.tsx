import i18next, { InitOptions, TOptions } from 'i18next';
import resourcesToBackend from 'i18next-resources-to-backend';
// import { z } from 'zod';
// import { ZodI18nMapOption, makeZodI18nMap } from 'zod-i18n-map';

import { languageCodes } from '@swo/countries/languageCodes';

const i18n: ReturnType<typeof i18next.createInstance> = i18next.createInstance();

i18n.use(
  resourcesToBackend(async (language: string) => {
    const validLanguage = languageCodes.find(l => l.includes(language))?.replace('-', '_');
    if (!validLanguage) {
      return;
    }

    const resource = language.startsWith('en') ? await import(`./en.json`) : await import(`./${validLanguage}/${validLanguage}.json`);

    const translations = resource.default ?? {};

    console.log(`Loaded translations for language ${language}:`, translations);

    i18n.addResourceBundle(language, 'mpt', translations, true);

    return translations;
  })
);
i18n.on('failedLoading', (lng, _ns, msg) => console.error(`[i18n] Failed to load language ${lng} with error:`, msg));
i18n.init({
  lng: 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
  defaultNS: 'mpt',
  nsSeparator: ';',
  keySeparator: ':',
} as InitOptions);

// type typeOfi18nT = Extract<ZodI18nMapOption, 't'>;

// const t = ((key: string, options: TOptions) => {
//   if (key.indexOf('.') === -1) {
//     return i18n.t('shared:properties:' + key.replace(/\./g, ':'), options);
//   }
//   return i18n.t(key.replace(/\./g, ':'), options);
// }) as typeOfi18nT;

// z.setErrorMap(makeZodI18nMap({ t, ns: 'mpt', handlePath: { keyPrefix: 'shared.properties' } }));

export { i18n };

// Hot module replacement for translation file
// if ('hot' in module) {
//   // eslint-disable-next-line @typescript-eslint/ban-ts-comment
//   // @ts-ignore
//   module.hot.accept(`./en.json`, async () => {
//     await i18n.reloadResources('en', 'mpt');
//     await i18n.changeLanguage(i18n.language);
//   });
// }
