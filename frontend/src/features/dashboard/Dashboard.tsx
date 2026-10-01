import { Outlet } from "react-router-dom";

import { Navigation } from "@swo/design-system/navigation";

import { SEGMENTS } from "~features/dashboard/paths";
import { useFixedT } from "~shared/hooks/useFixedT";

import { DashboardFiltersProvider } from "./components/DashboardFiltersProvider";
import { FilterSidebar } from "./components/FilterSidebar";

export function Dashboard() {
  const tTabs = useFixedT("dashboard:tabs");

  const topBarItems = [
    { label: tTabs("adoption"), path: SEGMENTS.adoption },
    { label: tTabs("consumption"), path: SEGMENTS.consumption },
    { label: tTabs("health"), path: SEGMENTS.health },
    { label: tTabs("maturity"), path: SEGMENTS.maturity },
  ];

  return (
    <DashboardFiltersProvider>
      <div className={"ffc-workspace"}>
        <div className={"ffc-workspace__main"}>
          <Navigation.TopBar items={topBarItems} />
          <FilterSidebar />
          <Outlet />
        </div>
      </div>
    </DashboardFiltersProvider>
  );
}
