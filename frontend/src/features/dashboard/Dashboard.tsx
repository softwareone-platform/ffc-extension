import { useState } from "react";

import { Tab, Tabs } from "@swo/design-system/tabs";

import { useFixedT } from "~shared/hooks/useFixedT";

import { ComingSoonPanel } from "./components/ComingSoonPanel";
import { FilterSidebar } from "./components/FilterSidebar";
import { OrganisationFilter } from "./components/OrganisationFilter";
import { ConsumptionTab } from "./tabs/ConsumptionTab";
import { MaturityTab } from "./tabs/MaturityTab";

const TAB_IDS = {
  adoption: "adoption",
  consumption: "consumption",
  health: "health",
  maturity: "maturity",
} as const;

export function Dashboard() {
  const tTabs = useFixedT("dashboard:tabs");
  const [selectedTabId, setSelectedTabId] = useState<string>(TAB_IDS.consumption);

  return (
    <div className={"ffc-workspace"}>
      <FilterSidebar />
      <div className={"ffc-workspace__main ffc-tabbar"}>
        <div className={"ffc-tabbar__actions"}>
          <OrganisationFilter />
        </div>
        <Tabs selectedTabId={selectedTabId} onTabChange={setSelectedTabId}>
          <Tab id={TAB_IDS.adoption} title={tTabs("adoption")}>
            <Tab.Content>
              <ComingSoonPanel title={tTabs("adoption")} />
            </Tab.Content>
          </Tab>
          <Tab id={TAB_IDS.consumption} title={tTabs("consumption")}>
            <Tab.Content>
              <ConsumptionTab />
            </Tab.Content>
          </Tab>
          <Tab id={TAB_IDS.health} title={tTabs("health")}>
            <Tab.Content>
              <ComingSoonPanel title={tTabs("health")} />
            </Tab.Content>
          </Tab>
          <Tab id={TAB_IDS.maturity} title={tTabs("maturity")}>
            <Tab.Content>
              <MaturityTab />
            </Tab.Content>
          </Tab>
        </Tabs>
      </div>
    </div>
  );
}
