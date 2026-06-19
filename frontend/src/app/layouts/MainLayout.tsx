import { Outlet, useMatch } from "react-router-dom";

import { Button } from "@swo/design-system/button";

import { PATHS } from "~app/paths";
import { EntitlementDetailsHeader } from "~features/entitlements/components/EntitlementDetailsHeader";
import { CreateEntitlementStandaloneModal } from "~entitlements/modal/CreateEntitlementStandaloneModal";
import { useModalToggle } from "~shared/hooks/useModalToggle";
import { OrganizationDetailsHeader } from "~features/organizations/components/OrganizationDetailsHeader";
import { PageShell, PageShellNavItem } from "~shared/components/page-shell";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useNotifyParentChildModal } from "~shared/hooks/useNotifyParentChildModal";
import { StandaloneShellProvider } from "~shared/providers/StandaloneShellContext";

const NAV_ITEMS: PageShellNavItem[] = [
  { path: PATHS.organizations.root, label: "Organizations" },
  { path: PATHS.entitlements.root, label: "Entitlements" },
];

export function MainLayout() {
  const tEntitlement = useFixedT("entitlement");
  const { isOpen, open, close } = useModalToggle();

  const entitlementMatch = useMatch(PATHS.entitlements.detailMatch);
  const organizationMatch = useMatch(PATHS.organizations.detailMatch);

  useNotifyParentChildModal(isOpen);

  const header = renderHeader();

  function renderHeader() {
    if (entitlementMatch?.params.entitlementId) {
      return (
        <EntitlementDetailsHeader
          entitlementId={entitlementMatch.params.entitlementId}
          backUrl={PATHS.entitlements.root}
        />
      );
    }
    if (organizationMatch?.params.organizationId) {
      return (
        <OrganizationDetailsHeader
          organizationId={organizationMatch.params.organizationId}
          backUrl={PATHS.organizations.root}
        />
      );
    }
    return (
      <PageShell.Header
        items={NAV_ITEMS}
        actions={
          <Button type="primary" onClick={open} testId="add-entitlement-button">
            {tEntitlement("add_entitlement")}
          </Button>
        }
      />
    );
  }

  return (
    <StandaloneShellProvider>
      <PageShell>
        {header}
        <PageShell.Content>
          <Outlet />
        </PageShell.Content>
      </PageShell>
      <CreateEntitlementStandaloneModal isOpen={isOpen} onClose={close} />
    </StandaloneShellProvider>
  );
}
