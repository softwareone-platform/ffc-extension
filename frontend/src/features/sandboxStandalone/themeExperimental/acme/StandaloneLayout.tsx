import { Outlet } from "react-router-dom";

import { Navigation } from "@swo/design-system/navigation";

import { SandboxHeaderActions } from "~features/sandboxStandalone/components/SandboxHeaderActions";
import { ConsentModal } from "~features/sandboxStandalone/modals/ConsentModal";
import { sideNavGroups } from "~features/sandboxStandalone/navigation";

import "./StandaloneLayout.scss";

export function StandaloneLayout() {
  return (
    <>
      <ConsentModal appName="the Sandbox Standalone" />
      <Navigation>
        <Navigation.SideNav level={2} groups={sideNavGroups} />
        <Navigation.HeaderBar title="Acme theme" subtitle="Version: 0.0.1">
          <Navigation.HeaderBar.Actions>
            <SandboxHeaderActions />
          </Navigation.HeaderBar.Actions>
        </Navigation.HeaderBar>
        <Navigation.Content>
          <Outlet />
        </Navigation.Content>
      </Navigation>
    </>
  );
}
