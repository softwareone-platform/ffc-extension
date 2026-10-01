import { useId, useState } from "react";

import { Button } from "@swo/design-system/button";
import { Checkbox } from "@swo/design-system/checkbox";
import { DatePicker } from "@swo/design-system/date-picker";
import { Divider } from "@swo/design-system/divider";
import { Icon } from "@swo/design-system/icon";
import { Popover } from "@swo/design-system/popover";

import { useFixedT } from "~shared/hooks/useFixedT";

const ORGANISATION_STATUSES = ["active", "paid", "trial", "terminated", "deleted"] as const;
const CLOUD_PROVIDERS = ["azure", "aws", "gcp"] as const;

type OrganisationStatus = (typeof ORGANISATION_STATUSES)[number];
type CloudProvider = (typeof CLOUD_PROVIDERS)[number];

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

// Default range: rolling 3-month window ending today. Computed once inside useState so the
// initial pair stays stable across re-renders.
function initialRange() {
  const to = new Date();
  const from = new Date(to);
  from.setMonth(from.getMonth() - 3);
  return { from, to };
}

/**
 * Global filter strip sitting above the dashboard tabs. Collapsed by default — a compact
 * header shows the active-filter counts and a chevron; expanded reveals a row of controls:
 * date range (From + To as one group, separated from the rest by a divider), then two
 * labelled multi-selects for organisation status and cloud provider.
 */
export function FilterSidebar() {
  const tFilters = useFixedT("dashboard:filters");
  const tStatus = useFixedT("dashboard:filters:status");
  const tProvider = useFixedT("dashboard:filters:provider");

  const [isCollapsed, setIsCollapsed] = useState(true);
  const [range, setRange] = useState(initialRange);
  const [statuses, setStatuses] = useState<OrganisationStatus[]>(["active"]);
  const [providers, setProviders] = useState<CloudProvider[]>([]);

  const statusOptions: MultiSelectOption<OrganisationStatus>[] = ORGANISATION_STATUSES.map(
    (status) => ({ value: status, label: tStatus(status) }),
  );
  const providerOptions: MultiSelectOption<CloudProvider>[] = CLOUD_PROVIDERS.map((provider) => ({
    value: provider,
    label: tProvider(provider),
  }));

  return (
    <section className={"ffc-filter-bar"} data-testid={"ffc-filter-bar"}>
      <button
        type={"button"}
        className={"ffc-filter-bar__header"}
        aria-expanded={!isCollapsed}
        aria-controls={"ffc-filter-bar-body"}
        onClick={() => setIsCollapsed((current) => !current)}
      >
        <Icon
          name={"arrow_forward_ios"}
          size={14}
          className={`ffc-filter-bar__chevron${isCollapsed ? "" : " ffc-filter-bar__chevron--open"}`}
        />
        <span className={"ffc-filter-bar__title"}>{tFilters("title")}</span>
        <span className={"ffc-filter-bar__summary"}>
          {tFilters("summary", {
            statusCount: statuses.length,
            providerCount: providers.length,
          })}
        </span>
      </button>

      <div
        id={"ffc-filter-bar-body"}
        className={`ffc-filter-bar__body${isCollapsed ? "" : " ffc-filter-bar__body--open"}`}
        aria-hidden={isCollapsed}
      >
        <div className={"ffc-filter-bar__body-inner"}>
          <div className={"ffc-filter-bar__group"}>
            <div className={"ffc-filter-bar__group-controls"}>
              <DatePicker<Date>
                label={tFilters("from")}
                value={range.from}
                maxDate={range.to}
                onChange={(from) => setRange((current) => ({ ...current, from }))}
              />
              <DatePicker<Date>
                label={tFilters("to")}
                value={range.to}
                minDate={range.from}
                onChange={(to) => setRange((current) => ({ ...current, to }))}
              />
            </div>
          </div>

          <Divider className={"ffc-filter-bar__divider"} />

          <div className={"ffc-filter-bar__group"}>
            <MultiSelect<OrganisationStatus>
              label={tFilters("organisationStatus")}
              placeholder={tFilters("selectStatuses")}
              options={statusOptions}
              value={statuses}
              onChange={setStatuses}
            />
          </div>

          <div className={"ffc-filter-bar__group"}>
            <MultiSelect<CloudProvider>
              label={tFilters("cloudProvider")}
              placeholder={tFilters("selectProviders")}
              options={providerOptions}
              value={providers}
              onChange={setProviders}
            />
          </div>

          <div className={"ffc-filter-bar__actions"}>
            <Button type={"primary"} onClick={() => undefined}>
              {tFilters("apply")}
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
