import { Outlet } from "react-router-dom";

import { Button } from "@swo/design-system/button";
import { Navigation } from "@swo/design-system/navigation";

import { sideNavGroups } from "~features/adobe/navigation";

export function AdobeLayout() {
  return (
    <Navigation>
      <Navigation.SideNav level={2} groups={sideNavGroups} />
      <Navigation.HeaderBar title="Adobe extension" subtitle="Version: 1.0.0">
        <Navigation.HeaderBar.Actions>
          <Button type="primary">Help</Button>
          <Button type="secondary">Terms & Conditions</Button>
        </Navigation.HeaderBar.Actions>
      </Navigation.HeaderBar>
      <Navigation.Content>
        <Outlet />
      </Navigation.Content>
    </Navigation>
  );
}
