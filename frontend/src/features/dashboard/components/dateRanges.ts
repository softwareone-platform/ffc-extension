import {
  endOfMonth,
  endOfYear,
  format,
  isSameDay,
  startOfDay,
  startOfMonth,
  startOfYear,
  subMonths,
  subYears,
} from "date-fns";

export type DateRangeValue = { from?: Date; to?: Date };

export const PRESET_KEYS = ["thisMonth", "lastMonth", "lastQuarter", "lastYear"] as const;
export type PresetKey = (typeof PRESET_KEYS)[number];

/** `dd.MM.yy` → "28.11.26", short enough to fit the sidebar. */
export const DISPLAY_DATE_FORMAT = "dd.MM.yy";

// Rolling 3-month window ending today. Day precision keeps the query key stable across renders.
export function defaultDateRange() {
  const to = startOfDay(new Date());
  return { from: subMonths(to, 3), to };
}

// Names a range the way the user picked it. Compared by calendar day because the URL keeps
// dates only, so a preset's `endOfMonth` comes back as that day's midnight.
export function describeRange(range: { from: Date; to: Date }): PresetKey | "default" | undefined {
  const matches = (candidate: DateRangeValue) =>
    !!candidate.from &&
    !!candidate.to &&
    isSameDay(candidate.from, range.from) &&
    isSameDay(candidate.to, range.to);
  if (matches(defaultDateRange())) {
    return "default";
  }
  return PRESET_KEYS.find((key) => matches(presetRange(key)));
}

export function presetRange(key: PresetKey): DateRangeValue {
  const now = new Date();
  switch (key) {
    case "thisMonth":
      return { from: startOfMonth(now), to: endOfMonth(now) };
    case "lastMonth": {
      const prev = subMonths(now, 1);
      return { from: startOfMonth(prev), to: endOfMonth(prev) };
    }
    case "lastQuarter": {
      // Last 4 full calendar months ending with the previous month (per product request).
      return {
        from: startOfMonth(subMonths(now, 4)),
        to: endOfMonth(subMonths(now, 1)),
      };
    }
    case "lastYear": {
      const prev = subYears(now, 1);
      return { from: startOfYear(prev), to: endOfYear(prev) };
    }
  }
}

export function formatRange(
  value: DateRangeValue,
  dateFormat = DISPLAY_DATE_FORMAT,
): string | undefined {
  if (!value.from && !value.to) {
    return undefined;
  }
  if (value.from && !value.to) {
    return `${format(value.from, dateFormat)} - …`;
  }
  if (!value.from && value.to) {
    return `… - ${format(value.to, dateFormat)}`;
  }
  return `${format(value.from as Date, dateFormat)} - ${format(value.to as Date, dateFormat)}`;
}
