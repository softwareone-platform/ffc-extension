import { Outlet, useNavigate } from "react-router-dom";

import { Button } from "@swo/design-system/button";
import { Navigation } from "@swo/design-system/navigation";

import { sideNavGroups } from "~features/sandboxStandalone/navigation";
import { PATHS } from "~features/sandboxStandalone/paths";
import { ConsentModal } from "~features/sandboxStandalone/modals/ConsentModal";

// Example theme override for the Adobe feature. Active when APP_THEME=acme.
// Imports resolve to the canonical feature/shared modules (the resolver does not
// redirect imports made from inside a theme directory).
export function AdobeLayout() {
  const navigate = useNavigate();

  return (
    <>
      <ConsentModal appName="the Sandbox Standalone (ACME)" />
      <Navigation>
        <Navigation.SideNav level={2} groups={sideNavGroups} />
        <Navigation.HeaderBar title="ACME · Adobe" subtitle="ACME theme">
          <Navigation.HeaderBar.Actions>
            <Button type="primary" onClick={() => navigate(PATHS.help)}>
              Help123
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
