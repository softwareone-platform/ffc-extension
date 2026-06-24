import { Outlet, useParams } from "react-router-dom";

import { Card } from "@swo/design-system/card";
import { Navigation } from "@swo/design-system/navigation";

import { SEGMENTS } from "~features/organizations/paths";
import { useOrganizationDetailsApi } from "~organizations/api";
import { useFixedT } from "~shared/hooks/useFixedT";

import { OrganizationsProvider } from "../providers/OrganizationsProvider";

// Inner content for organization details. Outer chrome comes from MainLayout
// (standalone) or DetailsLayout (per-feature entry).
export function OrganizationDetailsContent() {
  const { organizationId } = useParams();
  const { data: entity } = useOrganizationDetailsApi(organizationId);
  const tDetails = useFixedT("organization:details");

  const topBarItems = [
    { label: tDetails("general:title"), path: SEGMENTS.general },
    { label: tDetails("dataSources:title"), path: SEGMENTS.dataSources },
    { label: tDetails("users:title"), path: SEGMENTS.users },
  ];

  return (
    <>
      <Navigation.TopBar items={topBarItems} />
      <OrganizationsProvider organization={entity!}>
        <Card>
          <Outlet />
        </Card>
      </OrganizationsProvider>
    </>
  );
}
