import { renderHook } from "@testing-library/react";
import { de } from "date-fns/locale";

import { NO_VALUE, useLocalisation } from "@swo/design-system/utils";

import { useDateDistance } from "./useDateDistance";

type Localisation = ReturnType<typeof useLocalisation>;

const mockUseLocalisation = jest.mocked(useLocalisation);
const NOW = new Date("2026-06-15T12:00:00Z");

function getDateDistance() {
  return renderHook(() => useDateDistance()).result.current;
}

describe("useDateDistance", () => {
  beforeEach(() => {
    jest.useFakeTimers({ now: NOW });
    mockUseLocalisation.mockReturnValue({} as Localisation);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it.each([
    ["an empty string", ""],
    ["an invalid date", "not-a-date"],
    ["a pre-1800 sentinel date", "0001-01-01T00:00:00Z"],
  ])("returns NO_VALUE for %s", (_, value) => {
    expect(getDateDistance()(value)).toBe(NO_VALUE);
  });

  it("formats past dates as a relative distance with an English suffix by default", () => {
    expect(getDateDistance()("2026-06-12T12:00:00Z")).toBe("3 days ago");
  });

  it("accepts Date instances", () => {
    expect(getDateDistance()(new Date("2026-06-15T14:00:00Z"))).toBe("in about 2 hours");
  });

  it("formats the distance in the localisation's locale", () => {
    mockUseLocalisation.mockReturnValue({ locale: de } as unknown as Localisation);

    expect(getDateDistance()("2026-06-12T12:00:00Z")).toBe("vor 3 Tagen");
  });

  it("falls back to English for an unsupported locale", () => {
    mockUseLocalisation.mockReturnValue({ locale: { code: "fr" } } as unknown as Localisation);

    expect(getDateDistance()("2026-06-12T12:00:00Z")).toBe("3 days ago");
  });
});
