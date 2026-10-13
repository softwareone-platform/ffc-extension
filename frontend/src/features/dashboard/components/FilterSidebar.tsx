import { useState } from "react";

import Select, { MultiValue } from "react-select";

import { Button } from "@swo/design-system/button";
import { Divider } from "@swo/design-system/divider";
import { Icon } from "@swo/design-system/icon";

import { useFixedT } from "~shared/hooks/useFixedT";

import {
  CLOUD_PROVIDERS,
  CloudProvider,
  ORGANISATION_STATUSES,
  OrganisationStatus,
} from "../api/model";
import { DashboardFilters, useDashboardFilters } from "./DashboardFiltersContext";
import { DateRangePicker } from "./DateRangePicker";

type SelectOption<T extends string> = { value: T; label: string };

/**
 * Persistent left-column filter panel for the dashboard, modelled on the SWO `Navigation.SideNav`
 * (250px expanded / 72px collapsed with a floating circular collapse button on the right edge).
 * The date range uses `react-day-picker` and the multi-selects use `react-select` — the SWO DS
 * ships neither primitive. Changes stay in a local draft until Apply commits them to
 * `DashboardFiltersContext`.
 */
export function FilterSidebar() {
  const tFilters = useFixedT("dashboard:filters");
  const tStatus = useFixedT("dashboard:filters:status");
  const tProvider = useFixedT("dashboard:filters:provider");

  const { filters, setFilters } = useDashboardFilters();
  const [draft, setDraft] = useState<DashboardFilters>(filters);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const statusOptions: SelectOption<OrganisationStatus>[] = ORGANISATION_STATUSES.map((status) => ({
    value: status,
    label: tStatus(status),
  }));
  const providerOptions: SelectOption<CloudProvider>[] = CLOUD_PROVIDERS.map((provider) => ({
    value: provider,
    label: tProvider(provider),
  }));

  function apply() {
    setFilters(draft);
  }

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
              value={{ from: draft.from, to: draft.to }}
              onChange={(range) =>
                setDraft((current) => ({
                  ...current,
                  from: range.from ?? current.from,
                  to: range.to ?? current.to,
                }))
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
              value={selectedOptions(statusOptions, draft.statuses)}
              onChange={(selected) =>
                setDraft((current) => ({ ...current, statuses: pickValues(selected) }))
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
              value={selectedOptions(providerOptions, draft.providers)}
              onChange={(selected) =>
                setDraft((current) => ({ ...current, providers: pickValues(selected) }))
              }
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
