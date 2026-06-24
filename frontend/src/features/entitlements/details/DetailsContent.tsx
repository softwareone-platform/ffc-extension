import { Outlet } from "react-router-dom";

import { Card } from "@swo/design-system/card";
import { Navigation } from "@swo/design-system/navigation";

import { SEGMENTS } from "~features/entitlements/paths";
import { useFixedT } from "~shared/hooks/useFixedT";

// Inner content for entitlement details. Outer chrome comes from MainLayout
// (standalone) or DetailsLayout (per-feature entry).
export function EntitlementDetailsContent() {
  const tDetails = useFixedT("entitlement:details");

  const topBarItems = [{ label: tDetails("general:title"), path: SEGMENTS.general }];

  return (
    <>
      <Navigation.TopBar items={topBarItems} />
      <Card>
        <Outlet />
      </Card>
    </>
  );
}
