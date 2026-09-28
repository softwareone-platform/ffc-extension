// The root manual mock at `__mocks__/@swo/design-system/utils.tsx` spreads
// `...jest.requireActual(...)` and overrides `NO_VALUE` / `useDesignSystemOptions` /
// `useLocalisation` / `DisplayValue`. Any spec-level `jest.mock("@swo/design-system/utils",
// () => ({...}))` fully REPLACES the global — silently dropping those exports.
//
// Two exports here:
//   - `mockDesignSystemUtilsGlobals` — just the constants + hook stubs. Spread it when a spec
//     needs to keep DisplayValue's real behaviour but override something else (e.g. useFormatDate).
//   - `mockDesignSystemUtils` — full replacement including a permissive DisplayValue mock
//     (`transform` runs when provided, otherwise `value ?? ""`). Use this when the spec renders
//     `<DisplayValue>` and doesn't need custom logic.
export const mockDesignSystemUtilsGlobals = {
  NO_VALUE: "—",
  useDesignSystemOptions: jest.fn().mockReturnValue({
    languageCode: "en-GB",
    dateFormat: "dd MMM yyy",
    timeFormat: "HH:mm",
    inputDateFormat: "P",
  }),
  useLocalisation: jest.fn().mockReturnValue({
    formatDate: (date: unknown) => (date == null ? "" : String(date)),
    formatTime: (date: unknown) => (date == null ? "" : String(date)),
    formatCurrency: (value: number, { currency }: { currency?: string } = {}) =>
      `${value} ${currency ?? "UNK"}`.trim(),
  }),
};

type MockDisplayValueProps = {
  value?: unknown;
  transform?: (value: never) => unknown;
};

export const mockDesignSystemUtils = {
  ...mockDesignSystemUtilsGlobals,
  DisplayValue: ({ value, transform }: MockDisplayValueProps) => (
    <>{transform ? transform(value as never) : (value ?? "")}</>
  ),
};
