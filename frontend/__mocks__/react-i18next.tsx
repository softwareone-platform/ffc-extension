/* eslint-disable react-refresh/only-export-components */
// Global mock for react-i18next — identity `t` and Trans renders the i18n key.
// Auto-discovered by Jest because this file lives adjacent to node_modules.
module.exports = {
  useTranslation: () => ({
    t: (key: string) => key,
  }),
  Trans: jest.fn(({ i18nKey }: { i18nKey: string }) => <>{i18nKey}</>),
};
