import { Outlet, useParams } from "react-router-dom";

import { Navigation } from "@swo/design-system/navigation";

import { useOrganizationDetailsApi } from "~organizations/api";

import { OrganizationsProvider } from "../providers/OrganizationsProvider";

const TOP_BAR_ITEMS = [
  { label: "General", path: "general" },
  { label: "Data Sources", path: "data-sources" },
  { label: "Users", path: "users" },
];

/**
 * Inner content for organization details: entity-context highlights, sub-route
 * top bar and the matched child route. No `Navigation.HeaderBar` — the outer
 * chrome is owned by whoever mounts this (the standalone `MainLayout`, or the
 * full-chrome `DetailsLayout` used by the per-feature entry).
 *
 * Renders as direct children of `Navigation.Content` (provided by the parent
 * `PageShell.Content`).
 */
export function OrganizationDetailsContent() {
  const { organizationId } = useParams();
  const { data: entity } = useOrganizationDetailsApi(organizationId);

  return (
    <>
      <Navigation.TopBar  items={TOP_BAR_ITEMS} />
      <OrganizationsProvider organization={entity!}>
        <Outlet />
      </OrganizationsProvider>
    </>
  );
}
