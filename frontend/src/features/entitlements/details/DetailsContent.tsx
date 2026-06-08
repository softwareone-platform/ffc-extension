import { Outlet } from "react-router-dom";

import { Navigation } from "@swo/design-system/navigation";

import { SEGMENTS } from "~app/paths";

const TOP_BAR_ITEMS = [{ label: "General", path: SEGMENTS.general }];

// Inner content for entitlement details. Outer chrome comes from MainLayout
// (standalone) or DetailsLayout (per-feature entry).
export function EntitlementDetailsContent() {
  return (
    <>
      <Navigation.TopBar items={TOP_BAR_ITEMS} />
      <Outlet />
    </>
  );
}
