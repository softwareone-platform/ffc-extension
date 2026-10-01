import { renderHook } from "@testing-library/react";

import { useLocalisation } from "@swo/design-system/utils";

import { useFormatDate } from "./useFormatDate";

jest.mock("@swo/design-system/utils", () => {
  const actual = jest.requireActual("@swo/design-system/utils");
  return {
    ...actual,
    NO_VALUE: actual.NO_VALUE ?? "—",
    useLocalisation: jest.fn(),
  };
});

describe("useFormatDate", () => {
  it("formats valid dates with the localisation formatter", () => {
    const formatDate = jest.fn(() => "formatted-date");
    jest
      .mocked(useLocalisation)
      .mockReturnValue({ formatDate } as unknown as ReturnType<typeof useLocalisation>);

    const { result } = renderHook(() => useFormatDate());

    expect(result.current("2026-01-15T10:00:00Z")).toBe("formatted-date");
    expect(formatDate).toHaveBeenCalledWith(new Date("2026-01-15T10:00:00Z"));
  });

  it.each([
    ["invalid string", "not-a-date"],
    ["too early", "1700-06-01T12:00:00Z"],
    ["invalid Date", new Date("invalid")],
  ] as const)("returns NO_VALUE for %s", (_label, value) => {
    const formatDate = jest.fn();
    jest
      .mocked(useLocalisation)
      .mockReturnValue({ formatDate } as unknown as ReturnType<typeof useLocalisation>);

    const { result } = renderHook(() => useFormatDate());

    expect(result.current(value as string | Date)).toBe("—");
    expect(formatDate).not.toHaveBeenCalled();
  });
});
