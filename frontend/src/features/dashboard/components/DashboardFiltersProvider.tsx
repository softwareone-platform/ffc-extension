import { ReactNode, useCallback, useMemo } from "react";

import { useSearchParams } from "react-router-dom";

import {
  DashboardFilters,
  DashboardFiltersContext,
  parseDashboardFilters,
  toDashboardSearchParams,
} from "./DashboardFiltersContext";

// The URL is the single source of truth: a filter change rewrites the query string, and an
// edited or shared URL re-hydrates the filters.
export function DashboardFiltersProvider({ children }: { children: ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const search = searchParams.toString();

  // Keyed on the string so an unchanged query keeps the same filters object.
  const filters = useMemo(() => parseDashboardFilters(new URLSearchParams(search)), [search]);

  // `replace` keeps checkbox clicks out of the portal's session history (see App.tsx).
  const setFilters = useCallback(
    (next: DashboardFilters) => setSearchParams(toDashboardSearchParams(next), { replace: true }),
    [setSearchParams],
  );

  const value = useMemo(() => ({ filters, setFilters }), [filters, setFilters]);
  return (
    <DashboardFiltersContext.Provider value={value}>{children}</DashboardFiltersContext.Provider>
  );
}
