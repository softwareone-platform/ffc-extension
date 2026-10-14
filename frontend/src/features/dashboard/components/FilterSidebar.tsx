import { useState } from "react";

import Select, { MultiValue } from "react-select";

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
import { BILLING_COLOR, PROVIDER_COLOR, STATUS_COLOR } from "../chartConfig";
import { useDashboardFilters } from "./DashboardFiltersContext";
import { DateRangePicker } from "./DateRangePicker";

type SelectOption<T extends string> = { value: T; label: string; color: number };

function toCssColor(color: number) {
  return `#${color.toString(16).padStart(6, "0")}`;
}

// Renders the colour swatch + label used both inside the dropdown and in the selected chip —
// one definition keeps the two in sync automatically.
function renderOptionLabel<T extends string>(option: SelectOption<T>) {
  return (
    <span className={"ffc-select-option"}>
      <span
        className={"ffc-select-option__swatch"}
        style={{ background: toCssColor(option.color) }}
      />
      {option.label}
    </span>
  );
}

/**
 * Persistent left-column filter panel for the dashboard, modelled on the SWO `Navigation.SideNav`
 * (250px expanded / 72px collapsed with a floating circular collapse button on the right edge).
 * The date range uses `react-day-picker` and the multi-selects use `react-select` — the SWO DS
 * ships neither primitive. Every change commits directly to `DashboardFiltersContext` so the
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

  const statusOptions: SelectOption<OrganisationStatus>[] = ORGANISATION_STATUSES.map((status) => ({
    value: status,
    label: tStatus(status),
    color: STATUS_COLOR[status],
  }));
  const billingOptions: SelectOption<BillingStatus>[] = BILLING_STATUSES.map((status) => ({
    value: status,
    label: tBilling(status),
    color: BILLING_COLOR[status],
  }));
  const providerOptions: SelectOption<CloudProvider>[] = CLOUD_PROVIDERS.map((provider) => ({
    value: provider,
    label: tProvider(provider),
    color: PROVIDER_COLOR[provider],
  }));

  function selectedOptions<T extends string>(options: SelectOption<T>[], picks: T[]) {
    return options.filter((option) => picks.includes(option.value));
  }

  function pickValues<T extends string>(selected: MultiValue<SelectOption<T>>): T[] {
    return selected.map((option) => option.value);
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
            <DateRangePicker
              label={tFilters("dateRange")}
              placeholder={tFilters("pickDateRange")}
              value={{ from: filters.from, to: filters.to }}
              onChange={(range) =>
                setFilters({
                  ...filters,
                  from: range.from ?? filters.from,
                  to: range.to ?? filters.to,
                })
              }
            />
          </div>

          <Divider className={"ffc-filter-bar__divider"} />

          <div className={"ffc-filter-bar__group"}>
            <label className={"ffc-multiselect__label"}>{tFilters("organisationStatus")}</label>
            <Select<SelectOption<OrganisationStatus>, true>
              isMulti
              classNamePrefix={"ffc-select"}
              placeholder={tFilters("selectStatuses")}
              options={statusOptions}
              value={selectedOptions(statusOptions, filters.statuses)}
              formatOptionLabel={renderOptionLabel}
              onChange={(selected) => setFilters({ ...filters, statuses: pickValues(selected) })}
            />
          </div>

          <div className={"ffc-filter-bar__group"}>
            <label className={"ffc-multiselect__label"}>{tFilters("billingStatus")}</label>
            <Select<SelectOption<BillingStatus>, true>
              isMulti
              classNamePrefix={"ffc-select"}
              placeholder={tFilters("selectBillingStatuses")}
              options={billingOptions}
              value={selectedOptions(billingOptions, filters.billingStatuses)}
              formatOptionLabel={renderOptionLabel}
              onChange={(selected) =>
                setFilters({ ...filters, billingStatuses: pickValues(selected) })
              }
            />
          </div>

          <div className={"ffc-filter-bar__group"}>
            <label className={"ffc-multiselect__label"}>{tFilters("cloudProvider")}</label>
            <Select<SelectOption<CloudProvider>, true>
              isMulti
              classNamePrefix={"ffc-select"}
              placeholder={tFilters("selectProviders")}
              options={providerOptions}
              value={selectedOptions(providerOptions, filters.providers)}
              formatOptionLabel={renderOptionLabel}
              onChange={(selected) => setFilters({ ...filters, providers: pickValues(selected) })}
            />
          </div>
        </div>
      )}
    </aside>
  );
}
