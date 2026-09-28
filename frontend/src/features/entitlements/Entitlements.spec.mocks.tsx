import { Outlet } from "react-router-dom";

import type { RouteGuard } from "~shared/components/RouteGuard";

type MockRouteGuardProps = React.ComponentProps<typeof RouteGuard>;

export const mockRouteGuard = jest.fn() as jest.MockedFunction<
  (props: Pick<MockRouteGuardProps, "allowedRoles">) => void
>;

jest.mock("~shared/components/RouteGuard", () => ({
  RouteGuard: ({ children, allowedRoles }: MockRouteGuardProps) => {
    mockRouteGuard({ allowedRoles });
    return <div data-testid="route-guard">{children}</div>;
  },
}));

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
