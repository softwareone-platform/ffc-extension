import { Outlet, useMatch } from "react-router-dom";

import type { AccountType } from "~api/ffc-api-model";
import { PATHS } from "~app/paths";
import { EntitlementDetailsHeader } from "~features/entitlements/components/EntitlementDetailsHeader";
import { DataSourceDetailsHeader } from "~features/organizations/components/DataSourceDetailsHeader";
import { OrganizationDetailsHeader } from "~features/organizations/components/OrganizationDetailsHeader";
import { PageShell, PageShellNavItem } from "~shared/components/page-shell";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useUserRole } from "~shared/hooks/useUserRole";

export function MainLayout() {
  const tNav = useFixedT("shared:nav");
  const { role } = useUserRole();

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
    return item.role?.includes(role || "affiliate");
  });

  const entitlementMatch = useMatch(PATHS.entitlements.detailMatch);
  const organizationMatch = useMatch(PATHS.organizations.detailMatch);
  const dataSourceMatch = useMatch(PATHS.organizations.dataSourceMatch);

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
    if (dataSourceMatch?.params.dataSourceId && organizationMatch?.params.organizationId) {
      return (
        <DataSourceDetailsHeader
          organizationId={organizationMatch.params.organizationId}
          dataSourceId={dataSourceMatch.params.dataSourceId}
          backUrl={PATHS.organizations.dataSources(organizationMatch.params.organizationId)}
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
