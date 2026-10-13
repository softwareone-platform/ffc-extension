import { createContext, useContext } from "react";

import { CloudProvider, OrganisationStatus } from "../api/model";

export type DashboardFilters = {
  from: Date;
  to: Date;
  statuses: OrganisationStatus[];
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

// Appends the current dashboard filters to a path so the destination view (Organizations,
// Entitlements, …) can hydrate the same cohort. Preserves any per-link params the caller
// already encoded (e.g. `?status=active` on the Active KPI tile) by using the right separator.
export function withDashboardFilters(path: string, filters: DashboardFilters): string {
  const params = new URLSearchParams();
  if (filters.statuses.length > 0) {
    params.set("statuses", filters.statuses.join(","));
  }
  if (filters.providers.length > 0) {
    params.set("providers", filters.providers.join(","));
  }
  params.set("from", toIsoDate(filters.from));
  params.set("to", toIsoDate(filters.to));
  const query = params.toString();
  if (!query) return path;
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}${query}`;
}

function toIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}
