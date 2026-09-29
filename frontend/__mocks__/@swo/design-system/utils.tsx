/* eslint-disable react-refresh/only-export-components */
// Passes the real module through and overrides three hooks/components.
// module.exports keeps the requireActual spread intact.
import type { ComponentProps } from "react";

import type {
  DisplayValue,
  useDesignSystemOptions,
  useLocalisation,
} from "@swo/design-system/utils";

type DesignSystemOptions = ReturnType<typeof useDesignSystemOptions>;
type DesignSystemLocalisation = ReturnType<typeof useLocalisation>;
type DisplayValueProps = ComponentProps<typeof DisplayValue>;

const actual = jest.requireActual("@swo/design-system/utils");
const NO_VALUE = actual.NO_VALUE;

module.exports = {
  ...actual,
  useDesignSystemOptions: jest.fn().mockReturnValue({
    languageCode: "en-GB",
    dateFormat: "dd MMM yyy",
    timeFormat: "HH:mm",
    inputDateFormat: "P",
    numberFormat: "en-GB",
    timeZone: "UTC",
  } as DesignSystemOptions),
  useLocalisation: jest.fn().mockReturnValue({
    formatDate: (date: unknown) =>
      !date ? "" : typeof date === "string" ? date : date instanceof Date ? date.toISOString() : "",
    formatTime: (date: unknown) =>
      !date ? "" : typeof date === "string" ? date : date instanceof Date ? date.toISOString() : "",
    formatCurrency: (
      value: Parameters<DesignSystemLocalisation["formatCurrency"]>[0],
      { currency }: Parameters<DesignSystemLocalisation["formatCurrency"]>[1] = {},
    ) => `${value ?? ""} ${currency ?? "UNK"}`.trim(),
  } as DesignSystemLocalisation),
  DisplayValue: ({ value, transform, context, fallback }: DisplayValueProps) => {
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
