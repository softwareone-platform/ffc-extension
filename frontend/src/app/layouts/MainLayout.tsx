import { Outlet, useMatch } from "react-router-dom";

import { AccountType } from "~api/ffc-api-model/types.gen";
import { FEATURE_FLAGS } from "~app/featureFlags";
import { PATHS } from "~app/paths";
import { EntitlementDetailsHeader } from "~features/entitlements/components/EntitlementDetailsHeader";
import { OrganizationDetailsHeader } from "~features/organizations/components/OrganizationDetailsHeader";
import { PageShell, PageShellNavItem } from "~shared/components/page-shell";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useUserRole } from "~shared/hooks/useUserRole";

export function MainLayout() {
  const tNav = useFixedT("shared:nav");
  const { role } = useUserRole();

  const navItems: PageShellNavItem[] = [
    ...(FEATURE_FLAGS.dashboard
      ? [
          {
            path: PATHS.dashboard.root,
            label: tNav("dashboard"),
            role: ["admin", "operations", "affiliate"] as AccountType[],
          },
        ]
      : []),
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
    return item.role?.includes(role || "affiliate");
  });

  const entitlementMatch = useMatch(PATHS.entitlements.detailMatch);
  const organizationMatch = useMatch(PATHS.organizations.detailMatch);

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
    <PageShell>
      {header}
      <PageShell.Content>
        <Outlet />
      </PageShell.Content>
    </PageShell>
  );
}
