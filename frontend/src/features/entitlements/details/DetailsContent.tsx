import { Outlet } from "react-router-dom";

import { Card } from "@swo/design-system/card";
import { Navigation } from "@swo/design-system/navigation";

import { SEGMENTS } from "~features/entitlements/paths";

const TOP_BAR_ITEMS = [{ label: "General", path: SEGMENTS.general }];

// Inner content for entitlement details. Outer chrome comes from MainLayout
// (standalone) or DetailsLayout (per-feature entry).
export function EntitlementDetailsContent() {
  return (
    <>
      <Navigation.TopBar items={TOP_BAR_ITEMS} />
      <Card>
        <Outlet />
      </Card>
    </>
  );
}
