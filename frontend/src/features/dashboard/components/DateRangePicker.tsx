import { useId, useState } from "react";

import { DateRange, DayPicker } from "react-day-picker";

import { Button } from "@swo/design-system/button";
import { Icon } from "@swo/design-system/icon";
import { Popover } from "@swo/design-system/popover";

import { useFixedT } from "~shared/hooks/useFixedT";

import {
  DateRangeValue,
  DISPLAY_DATE_FORMAT,
  formatRange,
  PRESET_KEYS,
  PresetKey,
  presetRange,
} from "./dateRanges";

export type DateRangePickerProps = {
  label: string;
  placeholder: string;
  value: DateRangeValue;
  onChange: (next: DateRangeValue) => void;
  /** Format passed to `date-fns`. Defaults to `DISPLAY_DATE_FORMAT`. */
  dateFormat?: string;
};

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
  dateFormat = DISPLAY_DATE_FORMAT,
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

  const summary = formatRange(value, dateFormat) ?? placeholder;
  const presets = PRESET_KEYS.map((key) => ({ key, label: tPresets(key) }));

  function apply() {
    onChange(draft);
    setIsOpen(false);
  }

  // Presets are one-click shortcuts: commit the range + close the popover immediately rather
  // than requiring a second click on Apply.
  function applyPreset(key: PresetKey) {
    const range = presetRange(key);
    setDraft(range);
    onChange(range);
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
                  onClick={() => applyPreset(preset.key)}
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
