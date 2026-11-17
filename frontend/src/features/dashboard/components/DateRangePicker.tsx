import { useId, useState } from "react";

import { DatePicker } from "@swo/design-system/date-picker";
import { RadioButtonGroup } from "@swo/design-system/radio";

import { useFixedT } from "~shared/hooks/useFixedT";

import { defaultDateRange, describeRange, PRESET_KEYS, PresetKey, presetRange } from "./dateRanges";

type Choice = "default" | PresetKey | "custom";

export type DateRangePickerProps = {
  label: string;
  value: { from: Date; to: Date };
  onChange: (next: { from: Date; to: Date }) => void;
};

/**
 * Date range on SWO primitives — the design system ships no range picker. One radio group lists
 * the default window, the presets and "Custom date"; only the last reveals two `DatePicker`s,
 * each capping the other so the start can never pass the end.
 */
export function DateRangePicker({ label, value, onChange }: DateRangePickerProps) {
  const tFilters = useFixedT("dashboard:filters");
  const tPresets = useFixedT("dashboard:filters:presets");
  // Per-instance name: native radios with the same `name` form one group across the page.
  const groupName = useId();

  // The range itself says which option is on. "Custom date" is the one exception kept in
  // state, so picking it doesn't snap back while the dates still match a preset.
  const derived: Choice = describeRange(value) ?? "custom";
  const [isCustom, setIsCustom] = useState(derived === "custom");
  const choice = isCustom ? "custom" : derived;

  function select(next: Choice) {
    if (next === "custom") {
      setIsCustom(true);
      return;
    }
    setIsCustom(false);
    const range = next === "default" ? defaultDateRange() : presetRange(next);
    if (range.from && range.to) {
      onChange({ from: range.from, to: range.to });
    }
  }

  return (
    <div className={"ffc-date-range-picker"}>
      <RadioButtonGroup
        name={groupName}
        label={label}
        value={choice}
        options={[
          { value: "default", label: tPresets("default") },
          ...PRESET_KEYS.map((key) => ({ value: key, label: tPresets(key) })),
          { value: "custom", label: tFilters("customMode") },
        ]}
        onChange={(event) => select(event.target.value as Choice)}
      />

      {choice === "custom" && (
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
