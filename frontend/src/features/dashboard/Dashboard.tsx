import { Outlet } from "react-router-dom";

import { DashboardFiltersProvider } from "./components/DashboardFiltersProvider";
import { FilterSidebar } from "./components/FilterSidebar";

export function Dashboard() {
  return (
    <DashboardFiltersProvider>
      <div className={"ffc-workspace"}>
        <div className={"ffc-workspace__main"}>
          <FilterSidebar />
          <div className={"ffc-workspace__content"}>
            <Outlet />
          </div>
        </div>
      </div>
    </DashboardFiltersProvider>
  );
}
