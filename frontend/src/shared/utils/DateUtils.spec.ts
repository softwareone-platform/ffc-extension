import { getAllowedDeletionDate, isDeletionAllowed, isEpoch, toIsoDateString } from "./DateUtils";

describe("DateUtils", () => {
  it.each([
    [undefined, null],
    [null, null],
    ["invalid-date", null],
    ["2026-01-15T10:30:00Z", "2026-03-01T00:00:00.000Z"],
    ["2026-12-31T23:59:59Z", "2027-02-01T00:00:00.000Z"],
  ] as const)("getAllowedDeletionDate(%s)", (terminatedAt, expected) => {
    const result = getAllowedDeletionDate(terminatedAt);

    expect(result?.toISOString() ?? null).toBe(expected);
  });

  it.each([
    [undefined, "2026-03-02T00:00:00Z", false],
    ["2026-01-15T10:30:00Z", "2026-03-01T00:00:00Z", false],
    ["2026-01-15T10:30:00Z", "2026-03-01T00:00:00.001Z", true],
  ] as const)("isDeletionAllowed(%s, %s)", (terminatedAt, now, expected) => {
    expect(isDeletionAllowed(terminatedAt, new Date(now))).toBe(expected);
  });

  it("uses the current time when no comparison date is provided", () => {
    const result = isDeletionAllowed("2020-01-15T10:30:00Z");

    expect(result).toBe(true);
  });

  it("formats a date as an ISO calendar date", () => {
    expect(toIsoDateString(new Date(2026, 0, 2))).toBe("2026-01-02");
  });

  it.each([
    [null, true],
    [undefined, true],
    ["", true],
    ["invalid-date", true],
    [0, true],
    [new Date(0), true],
    ["1970-01-01T00:00:00.000Z", true],
    ["2026-01-15T10:30:00Z", false],
  ] as const)("isEpoch(%s)", (value, expected) => {
    expect(isEpoch(value)).toBe(expected);
  });
});
