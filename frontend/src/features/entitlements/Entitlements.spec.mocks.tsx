import { Outlet } from "react-router-dom";

import { mockRouteGuardModule } from "~test-utils/mocks/routeGuard";

export { mockRouteGuard } from "~test-utils/mocks/routeGuard";

jest.mock("~shared/components/RouteGuard", () => mockRouteGuardModule);

jest.mock("~features/entitlements/list/EntitlementsGrid", () => ({
  EntitlementsGrid: () => <div data-testid="entitlements-grid" />,
}));

jest.mock("~features/entitlements/details/general/General", () => ({
  EntitlementsGeneralDetails: () => <div data-testid="general" />,
}));

jest.mock("~features/entitlements/details/events/Events", () => ({
  EntitlementEventsDetails: () => <div data-testid="events" />,
}));

jest.mock("~features/entitlements/details/DetailsContent", () => ({
  EntitlementDetailsContent: () => (
    <div data-testid="details-content">
      <Outlet />
    </div>
  ),
}));
