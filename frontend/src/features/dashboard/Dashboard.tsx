import { Outlet } from "react-router-dom";

import { useIsFetching } from "@tanstack/react-query";

import { LoadingSpinner } from "@swo/design-system/loading-spinner";

import { DashboardFiltersProvider } from "./components/DashboardFiltersProvider";
import { FilterSidebar } from "./components/FilterSidebar";

export function Dashboard() {
  return (
    <DashboardFiltersProvider>
      <div className={"ffc-workspace"}>
        <div className={"ffc-workspace__main"}>
          <FilterSidebar />
          <DashboardContent />
        </div>
      </div>
    </DashboardFiltersProvider>
  );
}

// Lives inside the provider so `useIsFetching` can observe the dashboard queries. The overlay
// paints only while a `["Dashboard", ...]` query is in flight — react-query's
// `keepPreviousData` keeps the prior payload rendered underneath, so the overlay reads as a
// "refreshing" state rather than a full reload.
function DashboardContent() {
  const fetchingCount = useIsFetching({ queryKey: ["Dashboard"] });
  const isFetching = fetchingCount > 0;

  return (
    <div className={"ffc-workspace__content"}>
      <Outlet />
      {isFetching && (
        <div className={"ffc-workspace__overlay"} role={"status"} aria-live={"polite"}>
          <LoadingSpinner />
        </div>
      )}
    </div>
  );
}
