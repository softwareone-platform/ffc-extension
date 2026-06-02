import { useMemo } from "react";

import { Outlet, useLocation, useNavigate, useParams, useResolvedPath } from "react-router-dom";

import { Tab, Tabs } from "@swo/design-system/tabs";

import { useOrganizationDetailsApi } from "~organizations/api";

import { OrganizationsProvider } from "../providers/OrganizationsProvider";

const TABS: Array<{ id: string; label: string; segment: string }> = [
  { id: "general", label: "General", segment: "general" },
  { id: "data-sources", label: "Data Sources", segment: "data-sources" },
  { id: "users", label: "Users", segment: "users" },
];

/**
 * Inner layout for organization details: provider + sub-tabs + outlet.
 * No `PageShell` — the outer chrome is owned by whoever mounts this
 * (the standalone `MainLayout`, or the full-chrome `DetailsLayout` used
 * by the per-feature entry).
 */
export function OrganizationDetailsTabs() {
  const { organizationId } = useParams();
  const basePath = useResolvedPath("").pathname.replace(/\/$/, "");
  const { data: entity } = useOrganizationDetailsApi(organizationId);
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const tabs = useMemo(
    () =>
      TABS.map(({ id, label, segment }) => ({
        id,
        label,
        path: `${basePath}/${segment}`,
      })),
    [basePath],
  );

  const selectedTabId =
    tabs
      .filter((t) => pathname === t.path || pathname.startsWith(`${t.path}/`))
      .sort((a, b) => b.path.length - a.path.length)[0]?.id ??
    tabs[0]?.id ??
    "";

  return (
    <OrganizationsProvider organization={entity!}>
      <Tabs
        selectedTabId={selectedTabId}
        onTabChange={(id) => {
          const target = tabs.find((t) => t.id === id);
          if (target) navigate(target.path);
        }}
      >
        {tabs.map((tab) => (
          <Tab key={tab.id} id={tab.id} title={tab.label}>
            <Tab.Content>{tab.id === selectedTabId ? <Outlet /> : null}</Tab.Content>
          </Tab>
        ))}
      </Tabs>
    </OrganizationsProvider>
  );
}
