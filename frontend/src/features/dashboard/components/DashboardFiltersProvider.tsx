import { ReactNode, useMemo, useState } from "react";

import { DashboardFilters, DashboardFiltersContext } from "./DashboardFiltersContext";

// Rolling 3-month window ending today, matching the default previously hardcoded in the sidebar.
function initialFilters(): DashboardFilters {
  const to = new Date();
  const from = new Date(to);
  from.setMonth(from.getMonth() - 3);
  return { from, to, statuses: ["active"], providers: [] };
}

export function DashboardFiltersProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<DashboardFilters>(initialFilters);
  const value = useMemo(() => ({ filters, setFilters }), [filters]);
  return (
    <DashboardFiltersContext.Provider value={value}>{children}</DashboardFiltersContext.Provider>
  );
}
