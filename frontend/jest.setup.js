import {jest} from '@jest/globals';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Link: ({ children }) => <>{children}</>,
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: key => key,
  }),
  Trans: jest.fn(({ i18nKey }) => <>{i18nKey}</>),
}));

const identityFn = key => key;
jest.mock('~shared/hooks/useFixedT', () => {
  return { useFixedT: jest.fn(() => identityFn) };
});

jest.mock('@swo/design-system/utils', () => ({
  ...jest.requireActual('@swo/design-system/utils'),
  useDesignSystemOptions: jest
    .fn()
    .mockReturnValue({ languageCode: 'en-GB', dateFormat: 'dd MMM yyy', timeFormat: 'HH:mm', inputDateFormat: 'P' }),
  useLocalisation: jest.fn().mockReturnValue({
    formatDate: date => (!date ? '' : typeof date === 'string' ? date : date instanceof Date ? date.toISOString() : ''),
  }),
  DisplayValue: ({ value, transform, context, fallback }) => {
    const NO_VALUE = jest.requireActual('@swo/design-system/utils').NO_VALUE;
    if (value == null || (!value && context !== 'financial')) {
      return <>{fallback ?? NO_VALUE}</>;
    }

    if (typeof value === 'number' && !transform) {
      return <>{Intl.NumberFormat().format(value)}</>;
    }

    if (typeof value !== 'string' && !transform) {
      return <>{NO_VALUE}</>;
    }

    return <>{transform?.(value) ?? value}</>;
  },
}));

jest.setTimeout(5_000);
jest.useFakeTimers();

global.jest = jest;
