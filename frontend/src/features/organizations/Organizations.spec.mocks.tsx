import { Outlet } from "react-router-dom";

import { mockRouteGuardModule } from "~test-utils/mocks/routeGuard";

export { mockRouteGuard } from "~test-utils/mocks/routeGuard";

jest.mock("~shared/components/RouteGuard", () => mockRouteGuardModule);

jest.mock("~features/organizations/list/OrganizationsGrid", () => ({
  OrganizationsGrid: () => <div data-testid="organizations-grid" />,
}));

jest.mock("~features/organizations/details/DetailsContent", () => ({
  OrganizationDetailsContent: () => (
    <div data-testid="details-content">
      <Outlet />
    </div>
  ),
}));

jest.mock("~features/organizations/details/general/General", () => ({
  OrganizationGeneralDetails: () => <div data-testid="general" />,
}));

jest.mock("~features/organizations/details/data-sources/DataSources", () => ({
  OrganizationDataSources: () => <div data-testid="data-sources" />,
}));

jest.mock("~features/organizations/details/users/Users", () => ({
  OrganizationUsers: () => <div data-testid="users" />,
}));

jest.mock("~features/organizations/details/events/Events", () => ({
  OrganizationEventsDetails: () => <div data-testid="events" />,
}));
