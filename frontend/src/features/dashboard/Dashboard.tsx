import { Outlet } from "react-router-dom";

import { Navigation } from "@swo/design-system/navigation";

import { SEGMENTS } from "~features/dashboard/paths";
import { useFixedT } from "~shared/hooks/useFixedT";

import { FilterSidebar } from "./components/FilterSidebar";
import { OrganisationFilter } from "./components/OrganisationFilter";

export function Dashboard() {
  const tTabs = useFixedT("dashboard:tabs");

  const topBarItems = [
    { label: tTabs("adoption"), path: SEGMENTS.adoption },
    { label: tTabs("consumption"), path: SEGMENTS.consumption },
    { label: tTabs("health"), path: SEGMENTS.health },
    { label: tTabs("maturity"), path: SEGMENTS.maturity },
  ];

  return (
    <div className={"ffc-workspace"}>
      <FilterSidebar />
      <div className={"ffc-workspace__main ffc-tabbar"}>
        <div className={"ffc-tabbar__actions"}>
          <OrganisationFilter />
        </div>
        <Navigation.TopBar items={topBarItems} />
        <Outlet />
      </div>
    </div>
  );
}
