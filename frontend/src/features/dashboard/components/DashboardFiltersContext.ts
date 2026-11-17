import { createContext, useContext } from "react";

import { format, isValid, parse } from "date-fns";

import { LIST_PARAMS as ORGANIZATION_LIST_PARAMS } from "~organizations/paths";

import {
  BILLING_STATUSES,
  BillingStatus,
  CLOUD_PROVIDERS,
  CloudProvider,
  ORGANISATION_STATUSES,
  OrganisationStatus,
} from "../api/model";
import { defaultDateRange } from "./dateRanges";

export type DashboardFilters = {
  from: Date;
  to: Date;
  statuses: OrganisationStatus[];
  billingStatuses: BillingStatus[];
  providers: CloudProvider[];
};

export type DashboardFiltersContextValue = {
  filters: DashboardFilters;
  setFilters: (next: DashboardFilters) => void;
};

export const DashboardFiltersContext = createContext<DashboardFiltersContextValue | null>(null);

export function useDashboardFilters() {
  const ctx = useContext(DashboardFiltersContext);
  if (!ctx) {
    throw new Error("useDashboardFilters must be used within DashboardFiltersProvider");
  }
  return ctx;
}

// Statuses share the Organizations list param so the same value works on both pages.
// Billing picks travel as `billingStatuses` so they don't collide with the per-link
// `?billing=paid` param on the Trial vs Paid KPI tiles.
const PARAMS = {
  from: "from",
  to: "to",
  statuses: ORGANIZATION_LIST_PARAMS.statuses,
  billingStatuses: "billingStatuses",
  providers: "providers",
} as const;

const DATE_FORMAT = "yyyy-MM-dd";

function parseDate(value: string | null): Date | undefined {
  if (!value) return undefined;
  const date = parse(value, DATE_FORMAT, new Date());
  return isValid(date) ? date : undefined;
}

// Drops unknown values, so a hand-edited URL can't put an invalid pick into the filters.
function parseList<T extends string>(value: string | null, allowed: readonly T[]): T[] {
  if (!value) return [];
  const picks = new Set(value.split(","));
  return allowed.filter((item) => picks.has(item));
}

export function parseDashboardFilters(params: URLSearchParams): DashboardFilters {
  const defaults = defaultDateRange();
  return {
    from: parseDate(params.get(PARAMS.from)) ?? defaults.from,
    to: parseDate(params.get(PARAMS.to)) ?? defaults.to,
    statuses: parseList(params.get(PARAMS.statuses), ORGANISATION_STATUSES),
    billingStatuses: parseList(params.get(PARAMS.billingStatuses), BILLING_STATUSES),
    providers: parseList(params.get(PARAMS.providers), CLOUD_PROVIDERS),
  };
}

export function toDashboardSearchParams(filters: DashboardFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.statuses.length > 0) {
    params.set(PARAMS.statuses, filters.statuses.join(","));
  }
  if (filters.billingStatuses.length > 0) {
    params.set(PARAMS.billingStatuses, filters.billingStatuses.join(","));
  }
  if (filters.providers.length > 0) {
    params.set(PARAMS.providers, filters.providers.join(","));
  }
  // Local calendar date: `toISOString` would shift midnight into the previous UTC day.
  params.set(PARAMS.from, format(filters.from, DATE_FORMAT));
  params.set(PARAMS.to, format(filters.to, DATE_FORMAT));
  return params;
}

// Appends the current dashboard filters to a path so the destination view (Organizations,
// Entitlements, …) can hydrate the same cohort. Preserves any per-link params the caller
// already encoded (e.g. `?billing=paid` on a Trial vs Paid KPI tile) by using the right separator.
export function withDashboardFilters(path: string, filters: DashboardFilters): string {
  const query = toDashboardSearchParams(filters).toString();
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}${query}`;
}
