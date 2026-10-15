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

// The feature mocks expose how they were reached (`PUSH` / `REPLACE` / `POP`) so specs can assert
// the index redirect doesn't push a history entry (a push traps the browser Back button).
jest.mock("~features/organizations/Organizations", () => ({
  Organizations: () => {
    const { useNavigationType } = jest.requireActual("react-router-dom");
    return <div data-testid="organizations" data-navigation-type={useNavigationType()} />;
  },
}));

jest.mock("~features/entitlements/Entitlements", () => ({
  Entitlements: () => {
    const { useNavigationType } = jest.requireActual("react-router-dom");
    return <div data-testid="entitlements" data-navigation-type={useNavigationType()} />;
  },
}));
