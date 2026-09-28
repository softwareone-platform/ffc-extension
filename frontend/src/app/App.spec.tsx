import { screen } from "@testing-library/react";

import type { AccountType } from "~api/ffc-api-model";
import { renderWithRouter } from "~test-utils";

import { mockUseUserRole } from "./App.spec.mocks";

import { App } from "./App";

function renderApp(initialUrl: string) {
  return renderWithRouter(<App />, { initialUrl, routePath: "/*" });
}

function primeRole(role: AccountType | undefined) {
  mockUseUserRole.mockReturnValue({ user: null, role });
}

describe("App", () => {
  it("redirects the index route to entitlements for affiliate users", async () => {
    primeRole("affiliate");

    renderApp("/");

    expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
    expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
    expect(await screen.findByTestId("entitlements")).toBeInTheDocument();
  });

  it.each<AccountType>(["admin", "operations"])(
    "redirects the index route to organizations for role '%s'",
    async (role) => {
      primeRole(role);

      renderApp("/");

      expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
      expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
      expect(await screen.findByTestId("organizations")).toBeInTheDocument();
    },
  );

  it("redirects the index route to organizations when the role is missing", async () => {
    primeRole(undefined);

    renderApp("/");

    expect(await screen.findByTestId("organizations")).toBeInTheDocument();
  });

  it("renders nested organizations routes under MainLayout", async () => {
    primeRole("admin");

    renderApp("/organizations/anything");

    expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
    expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
    expect(await screen.findByTestId("organizations")).toBeInTheDocument();
  });
});
