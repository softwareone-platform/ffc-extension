import { useState } from "react";

import { Checkbox } from "@swo/design-system/checkbox";
import { Divider } from "@swo/design-system/divider";
import { Icon } from "@swo/design-system/icon";

import { useFixedT } from "~shared/hooks/useFixedT";

import {
  BILLING_STATUSES,
  BillingStatus,
  CLOUD_PROVIDERS,
  CloudProvider,
  ORGANISATION_STATUSES,
  OrganisationStatus,
} from "../api/model";
import { toCssColor } from "../chartColors";
import { BILLING_COLOR, PROVIDER_COLOR, STATUS_COLOR } from "../chartConfig";
import { useDashboardFilters } from "./DashboardFiltersContext";
import { DateRangePicker } from "./DateRangePicker";
import { describeRange } from "./dateRanges";
import { OrganizationsLink } from "./OrganizationsLink";

type FilterOption<T extends string> = { value: T; label: string; color: number };

type CheckboxGroupProps<T extends string> = {
  label: string;
  options: FilterOption<T>[];
  value: T[];
  onChange: (value: T[]) => void;
};

// Each option carries the same colour swatch the charts use, so the filter doubles as a legend.
function CheckboxGroup<T extends string>({
  label,
  options,
  value,
  onChange,
}: CheckboxGroupProps<T>) {
  function toggle(option: T, isChecked: boolean) {
    // Rebuild from `options` so the picked values keep the canonical order whatever the click order.
    onChange(
      options
        .map((item) => item.value)
        .filter((item) => (item === option ? isChecked : value.includes(item))),
    );
  }

  return (
    <fieldset className={"ffc-checkbox-group"}>
      <legend className={"ffc-multiselect__label"}>{label}</legend>
      {options.map((option) => (
        <Checkbox
          key={option.value}
          value={option.value}
          isChecked={value.includes(option.value)}
          onChange={(event) => toggle(option.value, event.target.checked)}
          label={
            <span className={"ffc-select-option"}>
              <span
                className={"ffc-select-option__swatch"}
                style={{ background: toCssColor(option.color) }}
              />
              {option.label}
            </span>
          }
        />
      ))}
    </fieldset>
  );
}

/**
 * Persistent left-column filter panel for the dashboard, modelled on the SWO `Navigation.SideNav`
 * (250px expanded / 72px collapsed with a floating circular collapse button on the right edge).
 * The date range is a pair of SWO `DatePicker`s with preset buttons, and the
 * multi-value filters are DS `Checkbox` groups. Every change commits directly to `DashboardFiltersContext` so the
 * dashboard updates live; the previous payload stays visible via react-query's
 * `keepPreviousData` so there's no flash while the next fetch is in flight.
 */
export function FilterSidebar() {
  const tFilters = useFixedT("dashboard:filters");
  const tStatus = useFixedT("dashboard:filters:status");
  const tBilling = useFixedT("dashboard:filters:billing");
  const tProvider = useFixedT("dashboard:filters:provider");

  const { filters, setFilters } = useDashboardFilters();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const statusOptions: FilterOption<OrganisationStatus>[] = ORGANISATION_STATUSES.map((status) => ({
    value: status,
    label: tStatus(status),
    color: STATUS_COLOR[status],
  }));
  const billingOptions: FilterOption<BillingStatus>[] = BILLING_STATUSES.map((status) => ({
    value: status,
    label: tBilling(status),
    color: BILLING_COLOR[status],
  }));
  const providerOptions: FilterOption<CloudProvider>[] = CLOUD_PROVIDERS.map((provider) => ({
    value: provider,
    label: tProvider(provider),
    color: PROVIDER_COLOR[provider],
  }));

  // Every ticked checkbox, plus the date range once it differs from the default — the same
  // things Reset clears.
  const activeCount =
    filters.statuses.length +
    filters.billingStatuses.length +
    filters.providers.length +
    (describeRange(filters) === "default" ? 0 : 1);

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
        {activeCount > 0 && (
          <span
            className={"ffc-filter-bar__badge"}
            role={"status"}
            aria-label={tFilters("activeCount", { count: activeCount })}
          >
            {activeCount}
          </span>
        )}
      </div>

      {!isCollapsed && (
        <div id={"ffc-filter-bar-body"} className={"ffc-filter-bar__body-inner"}>
          <div className={"ffc-filter-bar__group"}>
            {/* Remounts when the range returns to the default (e.g. Reset), so a "Custom date"
                choice left over from before doesn't stay selected. */}
            <DateRangePicker
              key={describeRange(filters) === "default" ? "default" : "picked"}
              label={tFilters("dateRange")}
              value={{ from: filters.from, to: filters.to }}
              onChange={(range) => setFilters({ ...filters, ...range })}
            />
          </div>

          <Divider className={"ffc-filter-bar__divider"} />

          <div className={"ffc-filter-bar__group"}>
            <CheckboxGroup
              label={tFilters("organisationStatus")}
              options={statusOptions}
              value={filters.statuses}
              onChange={(statuses) => setFilters({ ...filters, statuses })}
            />
          </div>

          <div className={"ffc-filter-bar__group"}>
            <CheckboxGroup
              label={tFilters("billingStatus")}
              options={billingOptions}
              value={filters.billingStatuses}
              onChange={(billingStatuses) => setFilters({ ...filters, billingStatuses })}
            />
          </div>

          <div className={"ffc-filter-bar__group"}>
            <CheckboxGroup
              label={tFilters("cloudProvider")}
              options={providerOptions}
              value={filters.providers}
              onChange={(providers) => setFilters({ ...filters, providers })}
            />
          </div>

          <Divider className={"ffc-filter-bar__divider"} />

          <OrganizationsLink />
        </div>
      )}
    </aside>
  );
}
