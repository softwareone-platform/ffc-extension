import { useId, useState } from "react";

import { Button } from "@swo/design-system/button";
import { Checkbox } from "@swo/design-system/checkbox";
import { DatePicker } from "@swo/design-system/date-picker";
import { Divider } from "@swo/design-system/divider";
import { Icon } from "@swo/design-system/icon";
import { Popover } from "@swo/design-system/popover";

import { useFixedT } from "~shared/hooks/useFixedT";

import {
  CLOUD_PROVIDERS,
  CloudProvider,
  ORGANISATION_STATUSES,
  OrganisationStatus,
} from "../api/model";
import { DashboardFilters, useDashboardFilters } from "./DashboardFiltersContext";

type MultiSelectOption<T extends string> = { value: T; label: string };

type MultiSelectProps<T extends string> = {
  label: string;
  placeholder: string;
  options: MultiSelectOption<T>[];
  value: T[];
  onChange: (next: T[]) => void;
};

/**
 * Lightweight multi-select built from DS primitives (`Popover` + `Checkbox`): a labelled
 * trigger button opens a popover with a checkbox list that stays open while the user ticks
 * multiple values. The DS `Dropdown` closes on each selection so it doesn't fit this use case.
 */
function MultiSelect<T extends string>({
  label,
  placeholder,
  options,
  value,
  onChange,
}: MultiSelectProps<T>) {
  const labelId = useId();
  const triggerId = useId();

  function toggle(entry: T) {
    onChange(value.includes(entry) ? value.filter((v) => v !== entry) : [...value, entry]);
  }

  const summary =
    value.length === 0
      ? placeholder
      : options
          .filter((option) => value.includes(option.value))
          .map((option) => option.label)
          .join(", ");

  return (
    <div className={"ffc-multiselect"}>
      <span id={labelId} className={"ffc-multiselect__label"}>
        {label}
      </span>
      <Popover trigger={"click"} keepOpenOnOutsideClick={false}>
        <Popover.Target>
          <button
            type={"button"}
            id={triggerId}
            className={"ffc-multiselect__trigger"}
            aria-labelledby={`${labelId} ${triggerId}`}
            aria-haspopup={"listbox"}
          >
            <span className={"ffc-multiselect__summary"}>{summary}</span>
            <Icon name={"expand_more"} size={16} />
          </button>
        </Popover.Target>
        <Popover.Content>
          <div className={"ffc-multiselect__list"} role={"listbox"} aria-multiselectable>
            {options.map((option) => (
              <Checkbox
                key={option.value}
                label={option.label}
                isChecked={value.includes(option.value)}
                onChange={() => toggle(option.value)}
              />
            ))}
          </div>
        </Popover.Content>
      </Popover>
    </div>
  );
}

/**
 * Persistent left-column filter panel for the dashboard, modelled on the SWO `Navigation.SideNav`
 * (250px expanded / 72px collapsed with a floating circular collapse button on the right edge).
 * Groups stack vertically — date range, organisation status, cloud provider — with Apply at the
 * bottom. Changes stay in a local draft until Apply commits them to `DashboardFiltersContext`.
 */
export function FilterSidebar() {
  const tFilters = useFixedT("dashboard:filters");
  const tStatus = useFixedT("dashboard:filters:status");
  const tProvider = useFixedT("dashboard:filters:provider");

  const { filters, setFilters } = useDashboardFilters();
  const [draft, setDraft] = useState<DashboardFilters>(filters);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const statusOptions: MultiSelectOption<OrganisationStatus>[] = ORGANISATION_STATUSES.map(
    (status) => ({ value: status, label: tStatus(status) }),
  );
  const providerOptions: MultiSelectOption<CloudProvider>[] = CLOUD_PROVIDERS.map((provider) => ({
    value: provider,
    label: tProvider(provider),
  }));

  function apply() {
    setFilters(draft);
  }

  return (
    <aside
      className={`ffc-filter-bar${isCollapsed ? " ffc-filter-bar--collapsed" : ""}`}
      data-testid={"ffc-filter-bar"}
    >
      <button
        type={"button"}
        className={"ffc-filter-bar__collapse-button"}
        aria-expanded={!isCollapsed}
        aria-controls={"ffc-filter-bar-body"}
        aria-label={tFilters(isCollapsed ? "expand" : "collapse")}
        onClick={() => setIsCollapsed((current) => !current)}
      >
        <Icon name={isCollapsed ? "arrow_forward_ios" : "arrow_back_ios"} size={12} />
      </button>

      <div className={"ffc-filter-bar__header"}>
        <Icon name={"settings"} size={20} className={"ffc-filter-bar__icon"} />
        {!isCollapsed && <span className={"ffc-filter-bar__title"}>{tFilters("title")}</span>}
      </div>

      {!isCollapsed && (
        <div id={"ffc-filter-bar-body"} className={"ffc-filter-bar__body-inner"}>
          <div className={"ffc-filter-bar__group"}>
            <DatePicker<Date>
              label={tFilters("from")}
              value={draft.from}
              maxDate={draft.to}
              onChange={(from) => setDraft((current) => ({ ...current, from }))}
            />
            <DatePicker<Date>
              label={tFilters("to")}
              value={draft.to}
              minDate={draft.from}
              onChange={(to) => setDraft((current) => ({ ...current, to }))}
            />
          </div>

          <Divider className={"ffc-filter-bar__divider"} />

          <div className={"ffc-filter-bar__group"}>
            <MultiSelect<OrganisationStatus>
              label={tFilters("organisationStatus")}
              placeholder={tFilters("selectStatuses")}
              options={statusOptions}
              value={draft.statuses}
              onChange={(statuses) => setDraft((current) => ({ ...current, statuses }))}
            />
          </div>

          <div className={"ffc-filter-bar__group"}>
            <MultiSelect<CloudProvider>
              label={tFilters("cloudProvider")}
              placeholder={tFilters("selectProviders")}
              options={providerOptions}
              value={draft.providers}
              onChange={(providers) => setDraft((current) => ({ ...current, providers }))}
            />
          </div>

          <div className={"ffc-filter-bar__actions"}>
            <Button type={"primary"} onClick={apply}>
              {tFilters("apply")}
            </Button>
          </div>
        </div>
      )}
    </aside>
  );
}
