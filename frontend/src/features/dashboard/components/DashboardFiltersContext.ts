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
