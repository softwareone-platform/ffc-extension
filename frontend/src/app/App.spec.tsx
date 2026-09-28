import { screen } from "@testing-library/react";

import type { AccountType } from "~api/ffc-api-model";
import { renderWithRouter } from "~test-utils";

import { mockUseUserRole } from "./App.spec.mocks";

import { App } from "./App";

describe("App", () => {
  it("redirects the index route to entitlements for affiliate users", async () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "affiliate" });

    renderWithRouter(<App />, { initialUrl: "/", routePath: "/*" });

    expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
    expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
    expect(await screen.findByTestId("entitlements")).toBeInTheDocument();
  });

  it.each<AccountType>(["admin", "operations"])(
    "redirects the index route to organizations for role '%s'",
    async (role) => {
      mockUseUserRole.mockReturnValue({ user: null, role });

      renderWithRouter(<App />, { initialUrl: "/", routePath: "/*" });

      expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
      expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
      expect(await screen.findByTestId("organizations")).toBeInTheDocument();
    },
  );

  it("redirects the index route to organizations when the role is missing", async () => {
    mockUseUserRole.mockReturnValue({ user: null, role: undefined });

    renderWithRouter(<App />, { initialUrl: "/", routePath: "/*" });

    expect(await screen.findByTestId("organizations")).toBeInTheDocument();
  });

  it("renders nested organizations routes under MainLayout", async () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });

    renderWithRouter(<App />, {
      initialUrl: "/organizations/anything",
      routePath: "/*",
    });

    expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
    expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
    expect(await screen.findByTestId("organizations")).toBeInTheDocument();
  });
});
