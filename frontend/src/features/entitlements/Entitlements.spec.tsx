import { screen, waitFor } from "@testing-library/react";

import { renderWithRouter } from "~test-utils";

import { mockRouteGuard } from "./Entitlements.spec.mocks";

import { Entitlements } from "./Entitlements";

function renderEntitlements(initialUrl: string) {
  return renderWithRouter(<Entitlements />, {
    initialUrl,
    routePath: "/entitlements/*",
  });
}

describe("Entitlements router", () => {
  it("guards the route tree with the admin, operations, and affiliate roles", async () => {
    renderEntitlements("/entitlements");

    await waitFor(() =>
      expect(mockRouteGuard).toHaveBeenCalledWith({
        allowedRoles: ["admin", "operations", "affiliate"],
      }),
    );
  });

  it("renders EntitlementsGrid at the index route", async () => {
    renderEntitlements("/entitlements");

    expect(await screen.findByTestId("entitlements-grid")).toBeInTheDocument();
  });

  it("redirects the bare detail route to the general tab inside the details shell", async () => {
    renderEntitlements("/entitlements/ent-1");

    expect(await screen.findByTestId("details-content")).toBeInTheDocument();
    expect(await screen.findByTestId("general")).toBeInTheDocument();
  });

  it.each([
    ["general", "/entitlements/ent-1/general", "general"],
    ["events", "/entitlements/ent-1/events", "events"],
  ] as const)(
    "renders the %s tab inside the entitlement details shell",
    async (_tab, url, testId) => {
      renderEntitlements(url);

      expect(await screen.findByTestId("details-content")).toBeInTheDocument();
      expect(await screen.findByTestId(testId)).toBeInTheDocument();
    },
  );
});
