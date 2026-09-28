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

async function expectShellAndPage(pageTestId: string) {
  expect(await screen.findByTestId("ffc-extension")).toBeInTheDocument();
  expect(await screen.findByTestId("main-layout")).toBeInTheDocument();
  expect(await screen.findByTestId(pageTestId)).toBeInTheDocument();
}

describe("App", () => {
  it("redirects the index route to entitlements for affiliate users", async () => {
    renderAppAt("/", "affiliate");

    await expectShellAndPage("entitlements");
  });

  it.each<AccountType>(["admin", "operations"])(
    "redirects the index route to organizations for role '%s'",
    async (role) => {
      renderAppAt("/", role);

      await expectShellAndPage("organizations");
    },
  );

  it("redirects the index route to organizations when the role is missing", async () => {
    renderAppAt("/", undefined);

    expect(await screen.findByTestId("organizations")).toBeInTheDocument();
  });

  it("renders nested organizations routes under MainLayout", async () => {
    renderAppAt("/organizations/anything", "admin");

    await expectShellAndPage("organizations");
  });
});
