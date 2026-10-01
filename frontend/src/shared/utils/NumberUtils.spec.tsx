import { renderHook } from "@testing-library/react";

import { useLocalisation } from "@swo/design-system/utils";

import { getNumberOrZero, useFormatMoney } from "./NumberUtils";

jest.mock("@swo/design-system/utils", () => ({
  useLocalisation: jest.fn(),
}));

describe("NumberUtils", () => {
  beforeEach(() => {
    jest.mocked(useLocalisation).mockReturnValue({
      formatCurrency: (value: number, { currency }: { currency?: string } = {}) =>
        `${value} ${currency ?? "UNK"}`,
    } as ReturnType<typeof useLocalisation>);
  });

  it.each([
    ["returns zero for null", null, 0],
    ["returns zero for undefined", undefined, 0],
    ["returns the provided number", 42, 42],
  ] as const)("getNumberOrZero %s", (_label, input, expected) => {
    expect(getNumberOrZero(input)).toBe(expected);
  });

  it("formats currency without showing the currency code", () => {
    const { result } = renderHook(() => useFormatMoney("USD"));

    expect(result.current(12)).toBe("12");
    expect(result.current(null)).toBe("0");
  });

  it("keeps the currency code when requested", () => {
    const { result } = renderHook(() => useFormatMoney("USD", true));

    expect(result.current(12)).toBe("12 USD");
  });

  it("falls back to the default currency token when no currency is provided", () => {
    const { result } = renderHook(() => useFormatMoney(undefined));

    expect(result.current(12)).toBe("12");
  });
});
