import { useState } from "react";

import { Button } from "@swo/design-system/button";
import { DatePicker } from "@swo/design-system/date-picker";
import { RadioButtonGroup } from "@swo/design-system/radio";

import { useFixedT } from "~shared/hooks/useFixedT";

import { describeRange, PRESET_KEYS, PresetKey, presetRange } from "./dateRanges";

type Mode = "presets" | "custom";

export type DateRangePickerProps = {
  label: string;
  value: { from: Date; to: Date };
  onChange: (next: { from: Date; to: Date }) => void;
};

/**
 * Date range on SWO primitives — the design system ships no range picker. A radio group picks
 * between one-click presets and a custom range made of two `DatePicker`s, each capping the other
 * so the start can never pass the end.
 */
export function DateRangePicker({ label, value, onChange }: DateRangePickerProps) {
  const tFilters = useFixedT("dashboard:filters");
  const tPresets = useFixedT("dashboard:filters:presets");
  const activePreset = describeRange(value);

  // Opens on Custom only when the range came from the date inputs (e.g. a shared URL);
  // after that the user's choice sticks, even when a custom range happens to match a preset.
  const [mode, setMode] = useState<Mode>(activePreset ? "presets" : "custom");

  function applyPreset(key: PresetKey) {
    const range = presetRange(key);
    if (range.from && range.to) {
      onChange({ from: range.from, to: range.to });
    }
  }

  return (
    <div className={"ffc-date-range-picker"}>
      <RadioButtonGroup
        name={"ffc-date-range-mode"}
        className={"ffc-date-range-picker__mode"}
        label={label}
        value={mode}
        options={[
          { value: "presets", label: tFilters("presetsMode") },
          { value: "custom", label: tFilters("customMode") },
        ]}
        onChange={(event) => setMode(event.target.value as Mode)}
      />

      {mode === "presets" ? (
        <div className={"ffc-date-range-picker__presets"} role={"group"} aria-label={label}>
          {PRESET_KEYS.map((key) => (
            <Button
              key={key}
              type={activePreset === key ? "primary" : "outline"}
              onClick={() => applyPreset(key)}
            >
              {tPresets(key)}
            </Button>
          ))}
        </div>
      ) : (
        <>
          <DatePicker<Date>
            label={tFilters("startDate")}
            value={value.from}
            maxDate={value.to}
            onChange={(from) => onChange({ ...value, from })}
          />
          <DatePicker<Date>
            label={tFilters("endDate")}
            value={value.to}
            minDate={value.from}
            onChange={(to) => onChange({ ...value, to })}
          />
        </>
      )}
    </div>
  );
}
