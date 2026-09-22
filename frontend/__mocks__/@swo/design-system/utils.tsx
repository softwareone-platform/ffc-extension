/* eslint-disable react-refresh/only-export-components */
// Passes the real module through and overrides three hooks/components.
// module.exports keeps the requireActual spread intact.
import type { ReactNode } from "react";

const actual = jest.requireActual("@swo/design-system/utils");
const NO_VALUE = actual.NO_VALUE;

module.exports = {
  ...actual,
  useDesignSystemOptions: jest.fn().mockReturnValue({
    languageCode: "en-GB",
    dateFormat: "dd MMM yyy",
    timeFormat: "HH:mm",
    inputDateFormat: "P",
  }),
  useLocalisation: jest.fn().mockReturnValue({
    formatDate: (date: unknown) =>
      !date
        ? ""
        : typeof date === "string"
          ? date
          : date instanceof Date
            ? date.toISOString()
            : "",
    formatTime: (date: unknown) =>
      !date
        ? ""
        : typeof date === "string"
          ? date
          : date instanceof Date
            ? date.toISOString()
            : "",
    formatCurrency: (value: number, {currency}: {currency?: string} = {}) =>
      `${value} ${currency ?? "UNK"}`.trim(),
  }),
  DisplayValue: ({
    value,
    transform,
    context,
    fallback,
  }: {
    value: unknown;
    transform?: (v: string) => ReactNode;
    context?: string;
    fallback?: ReactNode;
  }) => {
    if (value == null || (!value && context !== "financial")) {
      return <>{fallback ?? NO_VALUE}</>;
    }
    if (typeof value === "number" && !transform) {
      return <>{Intl.NumberFormat().format(value)}</>;
    }
    if (typeof value !== "string" && !transform) {
      return <>{NO_VALUE}</>;
    }
    return <>{transform?.(value as string) ?? value}</>;
  },
};
