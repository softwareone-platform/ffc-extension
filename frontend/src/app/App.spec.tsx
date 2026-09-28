import { screen } from "@testing-library/react";

import type { AccountType } from "~api/ffc-api-model";
import { renderWithRouter } from "~test-utils";
import { mockUseUserRole } from "~test-utils/mocks/userRole";

import "./App.spec.mocks";

import { App } from "./App";

function renderAppAt(initialUrl: string, role: AccountType | undefined) {
  mockUseUserRole.mockReturnValue({ user: null, role });
  renderWithRouter(<App />, { initialUrl, routePath: "/*" });
}

describe("App", () => {
  it("redirects the index route to entitlements for affiliate users", async () => {
    expect.assertions(3);
    renderAppAt("/", "affiliate");

    expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
    expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
    expect(await screen.findByTestId("entitlements")).toBeInTheDocument();
  });

  it.each<AccountType>(["admin", "operations"])(
    "redirects the index route to organizations for role '%s'",
    async (role) => {
      expect.assertions(3);
      renderAppAt("/", role);

      expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
      expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
      expect(await screen.findByTestId("organizations")).toBeInTheDocument();
    },
  );

  it("redirects the index route to organizations when the role is missing", async () => {
    expect.assertions(1);
    renderAppAt("/", undefined);

    expect(await screen.findByTestId("organizations")).toBeInTheDocument();
  });

  it("renders nested organizations routes under MainLayout", async () => {
    expect.assertions(3);
    renderAppAt("/organizations/anything", "admin");

    expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
    expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
    expect(await screen.findByTestId("organizations")).toBeInTheDocument();
  });
});
