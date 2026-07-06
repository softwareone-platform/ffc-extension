import { Outlet, useNavigate } from "react-router-dom";

import { Button } from "@swo/design-system/button";
import { Navigation } from "@swo/design-system/navigation";

import { sideNavGroups } from "~features/cloud-iq/navigation";
import { PATHS } from "~features/cloud-iq/paths";
import { ConsentModal } from "~shared/components/consent/ConsentModal";

export function CloudIqLayout() {
  const navigate = useNavigate();

  return (
    <>
      <ConsentModal appName="Cloud iQ" />
      <Navigation>
        <Navigation.SideNav level={2} groups={sideNavGroups} />
        <Navigation.HeaderBar title="Cloud iQ" subtitle="Version: 0.0.1">
          <Navigation.HeaderBar.Actions>
            <Button type="primary" onClick={() => navigate(PATHS.help)}>
              Help
            </Button>
            <Button type="secondary" onClick={() => navigate(PATHS.termsAndConditions)}>
              Terms & Conditions
            </Button>
          </Navigation.HeaderBar.Actions>
        </Navigation.HeaderBar>
        <Navigation.Content>
          <Outlet />
        </Navigation.Content>
      </Navigation>
    </>
  );
}
