import { Outlet } from "react-router-dom";

import { mockUserRoleModule, mockUseUserRole } from "~test-utils/mocks/userRole";

export { mockUseUserRole };

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

jest.mock("~app/layouts", () => ({
  MainLayout: () => (
    <div data-testid="main-layout">
      <Outlet />
    </div>
  ),
}));

jest.mock("~features/organizations/Organizations", () => ({
  Organizations: () => <div data-testid="organizations" />,
}));

jest.mock("~features/entitlements/Entitlements", () => ({
  Entitlements: () => <div data-testid="entitlements" />,
}));
