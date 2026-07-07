import { useContext } from "react";

import { Outlet, useMatch } from "react-router-dom";

import { AccountType } from "~api/ffc-api-model/types.gen";
import { PATHS } from "~app/paths";
import { CreateEntitlementStandaloneModal } from "~entitlements/modal/CreateEntitlementStandaloneModal";
import { EntitlementDetailsHeader } from "~features/entitlements/components/EntitlementDetailsHeader";
import { OrganizationDetailsHeader } from "~features/organizations/components/OrganizationDetailsHeader";
import { PageShell, PageShellNavItem } from "~shared/components/page-shell";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useModalToggle } from "~shared/hooks/useModalToggle";
import { useNotifyParentChildModal } from "~shared/hooks/useNotifyParentChildModal";
import { StandaloneShellProvider } from "~shared/providers/StandaloneShellContext";
import { UserContext } from "~shared/providers/UserContext";

export function MainLayout() {
  const tNav = useFixedT("shared:nav");
  const { isOpen, open, close } = useModalToggle();

  const user = useContext(UserContext);

  console.log("User account type:", user?.account.type); // Debugging line to check the user account type

  const navItems: PageShellNavItem[] = [
    {
      path: PATHS.organizations.root,
      label: tNav("organizations"),
      role: ["admin", "operations"] as AccountType[],
    },
    {
      path: PATHS.entitlements.root,
      label: tNav("entitlements"),
      role: ["admin", "operations", "affiliate"] as AccountType[],
    },
  ].filter((item) => {
    return item.role?.includes(user?.account.type || "affiliate");
  });

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
    return <PageShell.Header items={navItems} />;
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
