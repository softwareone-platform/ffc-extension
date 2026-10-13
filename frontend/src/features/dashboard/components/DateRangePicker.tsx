import { useId, useState } from "react";

import {
  endOfMonth,
  endOfQuarter,
  endOfYear,
  format,
  startOfMonth,
  startOfQuarter,
  startOfYear,
  subMonths,
  subQuarters,
  subYears,
} from "date-fns";
import { DateRange, DayPicker } from "react-day-picker";

import { Button } from "@swo/design-system/button";
import { Icon } from "@swo/design-system/icon";
import { Popover } from "@swo/design-system/popover";

import { useFixedT } from "~shared/hooks/useFixedT";

export type DateRangeValue = { from?: Date; to?: Date };

export type DateRangePickerProps = {
  label: string;
  placeholder: string;
  value: DateRangeValue;
  onChange: (next: DateRangeValue) => void;
  /** Format passed to `date-fns`. Default is `dd.MM.yyyy` → "28.11.2026". */
  dateFormat?: string;
};

type PresetKey = "thisMonth" | "lastMonth" | "lastQuarter" | "lastYear";

/**
 * Date-range trigger built from a SWO `Popover` + `react-day-picker` `DayPicker` in range mode.
 * The SWO design system doesn't ship a range picker; this wrapper mirrors the labelled-trigger
 * pattern of the existing MultiSelect and adds a column of preset ranges (This month, Last
 * month, Last quarter, Last year) plus an Apply button so a tentative range only commits to
 * the dashboard filters when the user confirms.
 */
export function DateRangePicker({
  label,
  placeholder,
  value,
  onChange,
  dateFormat = "dd.MM.yyyy",
}: DateRangePickerProps) {
  const tFilters = useFixedT("dashboard:filters");
  const tPresets = useFixedT("dashboard:filters:presets");
  const labelId = useId();
  const triggerId = useId();

  const [isOpen, setIsOpen] = useState(false);
  const [draft, setDraft] = useState<DateRangeValue>(value);

  // Resync the draft from the committed value as the popover opens — handled in the
  // open-change callback (not an effect) so React can batch both updates in one render.
  function handleOpenChange(open: boolean) {
    if (open) {
      setDraft(value);
    }
    setIsOpen(open);
  }

  const summary = formatRange(value, placeholder, dateFormat);
  const presets: { key: PresetKey; label: string }[] = [
    { key: "thisMonth", label: tPresets("thisMonth") },
    { key: "lastMonth", label: tPresets("lastMonth") },
    { key: "lastQuarter", label: tPresets("lastQuarter") },
    { key: "lastYear", label: tPresets("lastYear") },
  ];

  function apply() {
    onChange(draft);
    setIsOpen(false);
  }

  return (
    <div className={"ffc-multiselect"}>
      <span id={labelId} className={"ffc-multiselect__label"}>
        {label}
      </span>
      <Popover
        trigger={"click-manual"}
        keepOpenOnOutsideClick={false}
        isOpen={isOpen}
        isOpenChange={handleOpenChange}
      >
        <Popover.Target>
          <button
            type={"button"}
            id={triggerId}
            className={"ffc-multiselect__trigger"}
            aria-labelledby={`${labelId} ${triggerId}`}
          >
            <span className={"ffc-multiselect__summary"}>{summary}</span>
            <Icon name={"calendar"} size={16} />
          </button>
        </Popover.Target>
        <Popover.Content>
          <div className={"ffc-date-range"}>
            <div className={"ffc-date-range__presets"} role={"group"} aria-label={label}>
              {presets.map((preset) => (
                <button
                  key={preset.key}
                  type={"button"}
                  className={"ffc-date-range__preset"}
                  onClick={() => setDraft(presetRange(preset.key))}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <div className={"ffc-date-range__calendar"}>
              <DayPicker
                mode={"range"}
                numberOfMonths={2}
                selected={draft as DateRange}
                onSelect={(range) => setDraft(range ?? {})}
              />
              <div className={"ffc-date-range__actions"}>
                <Button type={"primary"} onClick={apply}>
                  {tFilters("apply")}
                </Button>
              </div>
            </div>
          </div>
        </Popover.Content>
      </Popover>
    </div>
  );
}

function presetRange(key: PresetKey): DateRangeValue {
  const now = new Date();
  switch (key) {
    case "thisMonth":
      return { from: startOfMonth(now), to: endOfMonth(now) };
    case "lastMonth": {
      const prev = subMonths(now, 1);
      return { from: startOfMonth(prev), to: endOfMonth(prev) };
    }
    case "lastQuarter": {
      const prev = subQuarters(now, 1);
      return { from: startOfQuarter(prev), to: endOfQuarter(prev) };
    }
    case "lastYear": {
      const prev = subYears(now, 1);
      return { from: startOfYear(prev), to: endOfYear(prev) };
    }
  }
}

function formatRange(value: DateRangeValue, placeholder: string, dateFormat: string): string {
  if (!value.from && !value.to) {
    return placeholder;
  }
  if (value.from && !value.to) {
    return `${format(value.from, dateFormat)} - …`;
  }
  if (!value.from && value.to) {
    return `… - ${format(value.to, dateFormat)}`;
  }
  return `${format(value.from as Date, dateFormat)} - ${format(value.to as Date, dateFormat)}`;
}
