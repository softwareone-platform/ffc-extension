import { Outlet, useParams } from "react-router-dom";

import { Navigation } from "@swo/design-system/navigation";

import { SEGMENTS } from "~app/paths";
import { useOrganizationDetailsApi } from "~organizations/api";

import { OrganizationsProvider } from "../providers/OrganizationsProvider";

const TOP_BAR_ITEMS = [
  { label: "General", path: SEGMENTS.general },
  { label: "Data Sources", path: SEGMENTS.dataSources },
  { label: "Users", path: SEGMENTS.users },
];

// Inner content for organization details. Outer chrome comes from MainLayout
// (standalone) or DetailsLayout (per-feature entry).
export function OrganizationDetailsContent() {
  const { organizationId } = useParams();
  const { data: entity } = useOrganizationDetailsApi(organizationId);

  return (
    <>
      <Navigation.TopBar items={TOP_BAR_ITEMS} />
      <OrganizationsProvider organization={entity!}>
        <Outlet />
      </OrganizationsProvider>
    </>
  );
}
