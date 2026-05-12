import { useCallback } from 'react';

import { useLocalisation } from '@swo/design-system/utils';

export function getNumberOrZero(value: number | null | undefined): number {
  if (value === null || value === undefined) {
    return 0;
  }
  return value;
}

export function useFormatMoney(currency?: string | null, isToShowCurrencyCode = false) {
  const { formatCurrency } = useLocalisation();

  return useCallback(
    (value?: number | null) => {
      if (isToShowCurrencyCode && currency) {
        return formatCurrency(value ?? 0, { currency: currency ?? 'UNK' }).replace(/\s/, ' ');
      }
      return formatCurrency(value ?? 0, { currency: currency ?? 'UNK' })
        .replace(currency ?? 'UNK', '')
        .replace(/\s/, ' ')
        .trim();
    },
    [currency, formatCurrency, isToShowCurrencyCode]
  );
}
