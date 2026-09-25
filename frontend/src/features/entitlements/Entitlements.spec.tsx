import type { ReactNode } from "react";

import { screen, waitFor } from "@testing-library/react";

import { renderWithRouter } from "~test-utils";

import { Entitlements } from "./Entitlements";

const mockRouteGuard = jest.fn() as jest.MockedFunction<
  (props: { allowedRoles: readonly string[] }) => void
>;

jest.mock("~shared/components/RouteGuard", () => ({
  RouteGuard: ({
    children,
    allowedRoles,
  }: {
    children: ReactNode;
    allowedRoles: readonly string[];
  }) => {
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
  EntitlementDetailsContent: () => <div data-testid="details-content" />,
}));

describe("Entitlements router", () => {
  it("guards the route tree with the admin, operations, and affiliate roles", async () => {
    renderWithRouter(<Entitlements />, { initialUrl: "/", routePath: "/*" });

    await waitFor(() =>
      expect(mockRouteGuard).toHaveBeenCalledWith({
        allowedRoles: ["admin", "operations", "affiliate"],
      }),
    );
  });

  it("renders EntitlementsGrid at the index route", async () => {
    renderWithRouter(<Entitlements />, { initialUrl: "/", routePath: "/*" });

    expect(await screen.findByTestId("entitlements-grid")).toBeInTheDocument();
  });
});
