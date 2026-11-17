import { useId } from "react";

import { useNavigate } from "react-router-dom";

import { Button } from "@swo/design-system/button";

import { LIST_PARAMS, PATHS as ORGANIZATION_PATHS } from "~organizations/paths";
import { useFixedT } from "~shared/hooks/useFixedT";

import { toCssColor } from "../chartColors";
import { BILLING_COLOR, PROVIDER_COLOR, STATUS_COLOR } from "../chartConfig";
import { useDashboardFilters } from "./DashboardFiltersContext";
import { describeRange, formatRange } from "./dateRanges";

type SummaryValue = { key: string; label: string; color?: number };
// `isApplied` is false for filters the Organizations list has no field for.
type SummarySection = { label: string; values: SummaryValue[]; isApplied: boolean };

/**
 * Sidebar footer that opens the Organizations list with the dashboard's status picks applied,
 * followed by a summary of every filter that differs from its default. Only the status filter
 * carries over; the rest are greyed out and marked as not applied.
 */
export function OrganizationsLink() {
  const tLink = useFixedT("dashboard:filters:organizationsLink");
  const tFilters = useFixedT("dashboard:filters");
  const tStatus = useFixedT("dashboard:filters:status");
  const tBilling = useFixedT("dashboard:filters:billing");
  const tProvider = useFixedT("dashboard:filters:provider");
  const tPresets = useFixedT("dashboard:filters:presets");
  const navigate = useNavigate();
  const summaryId = useId();

  const { filters } = useDashboardFilters();
  const statuses = filters.statuses;

  const rangeKind = describeRange(filters);
  const rangeLabel =
    rangeKind && rangeKind !== "default" ? tPresets(rangeKind) : formatRange(filters);

  // Only filters that differ from their default get a section; colours match the charts.
  const sections: SummarySection[] = [
    {
      label: tFilters("dateRange"),
      isApplied: false,
      values: rangeKind === "default" ? [] : [{ key: "range", label: rangeLabel ?? "" }],
    },
    {
      label: tFilters("organisationStatus"),
      isApplied: true,
      values: statuses.map((status) => ({
        key: status,
        label: tStatus(status),
        color: STATUS_COLOR[status],
      })),
    },
    {
      label: tFilters("billingStatus"),
      isApplied: false,
      values: filters.billingStatuses.map((status) => ({
        key: status,
        label: tBilling(status),
        color: BILLING_COLOR[status],
      })),
    },
    {
      label: tFilters("cloudProvider"),
      isApplied: false,
      values: filters.providers.map((provider) => ({
        key: provider,
        label: tProvider(provider),
        color: PROVIDER_COLOR[provider],
      })),
    },
  ].filter((section) => section.values.length > 0);

  function openOrganizations() {
    const query = new URLSearchParams();
    if (statuses.length > 0) {
      query.set(LIST_PARAMS.statuses, statuses.join(","));
    }
    const search = query.toString();
    navigate(search ? `${ORGANIZATION_PATHS.root}?${search}` : ORGANIZATION_PATHS.root);
  }

  return (
    <div className={"ffc-organizations-link"}>
      <Button
        type={"primary"}
        className={"ffc-organizations-link__button"}
        onClick={openOrganizations}
        aria-describedby={summaryId}
      >
        {tLink("open")}
      </Button>

      <div id={summaryId} className={"ffc-organizations-link__summary"}>
        {sections.length === 0 ? (
          <span className={"ffc-organizations-link__empty"}>{tLink("noFilters")}</span>
        ) : (
          sections.map((section) => (
            <div
              key={section.label}
              className={`ffc-organizations-link__section${section.isApplied ? "" : " ffc-organizations-link__section--ignored"}`}
            >
              <span className={"ffc-organizations-link__label"}>
                {section.label}
                {!section.isApplied && (
                  <span className={"ffc-organizations-link__tag"}>{tLink("notApplied")}</span>
                )}
              </span>
              <ul className={"ffc-organizations-link__values"}>
                {section.values.map((value) => (
                  <li key={value.key} className={"ffc-organizations-link__value"}>
                    {value.color !== undefined && (
                      <span
                        className={"ffc-select-option__swatch"}
                        style={{ background: toCssColor(value.color) }}
                      />
                    )}
                    {value.label}
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
