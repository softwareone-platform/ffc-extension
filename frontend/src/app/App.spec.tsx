import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import type { AccountType } from "~api/ffc-api-model";
import { mockUserRoleModule, mockUseUserRole } from "~test-utils/mocks/userRole";

import { App } from "./App";

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

jest.mock("~app/layouts", () => ({
  MainLayout: () => (
    <div data-testid="main-layout">
      <div data-testid="outlet-placeholder">outlet</div>
    </div>
  ),
}));

jest.mock("~features/organizations/Organizations", () => ({
  Organizations: () => <div data-testid="organizations" />,
}));

jest.mock("~features/entitlements/Entitlements", () => ({
  Entitlements: () => <div data-testid="entitlements" />,
}));

function renderApp(initialUrl: string) {
  return render(
    <MemoryRouter initialEntries={[initialUrl]}>
      <App />
    </MemoryRouter>,
  );
}

function primeRole(role: AccountType | undefined) {
  mockUseUserRole.mockReturnValue({ user: null, role });
}

describe("App", () => {
  it("redirects the index route to entitlements for affiliate users", async () => {
    primeRole("affiliate");

    renderApp("/");

    // The redirect lands on /entitlements, which sits under the layout wrapper.
    expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
  });

  it.each<AccountType>(["admin", "operations"])(
    "redirects the index route to organizations for role '%s'",
    async (role) => {
      primeRole(role);

      renderApp("/");

      expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
    },
  );

  it("mounts MainLayout under the ffc-extension wrapper on nested routes", async () => {
    primeRole("admin");

    renderApp("/organizations/anything");

    expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
    expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
  });
});
