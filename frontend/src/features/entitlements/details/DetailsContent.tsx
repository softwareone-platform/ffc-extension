import { Outlet } from "react-router-dom";

import { Navigation } from "@swo/design-system/navigation";

const TOP_BAR_ITEMS = [{ label: "General", path: "general" }];

/**
 * Inner content for entitlement details: entity-context highlights, sub-route
 * top bar and the matched child route. No `Navigation.HeaderBar` — the outer
 * chrome is owned by whoever mounts this (the standalone `MainLayout`, or the
 * full-chrome `DetailsLayout` used by the per-feature entry).
 *
 * Renders as direct children of `Navigation.Content` (provided by the parent
 * `PageShell.Content`).
 */
export function EntitlementDetailsContent() {
  return (
    <>
      <Navigation.TopBar items={TOP_BAR_ITEMS} />
      <Outlet />
    </>
  );
}
