import type { ReactNode } from "react";

import { screen, waitFor } from "@testing-library/react";

import { renderWithRouter } from "~test-utils";

import { Organizations } from "./Organizations";

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

jest.mock("~features/organizations/list/OrganizationsGrid", () => ({
  OrganizationsGrid: () => <div data-testid="organizations-grid" />,
}));

jest.mock("~features/organizations/details/DetailsContent", () => ({
  OrganizationDetailsContent: () => <div data-testid="details-content" />,
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

describe("Organizations router", () => {
  it("guards the route tree with the admin and operations roles", async () => {
    renderWithRouter(<Organizations />, { initialUrl: "/", routePath: "/*" });

    await waitFor(() =>
      expect(mockRouteGuard).toHaveBeenCalledWith({ allowedRoles: ["admin", "operations"] }),
    );
  });

  it("renders OrganizationsGrid at the index route", async () => {
    renderWithRouter(<Organizations />, { initialUrl: "/", routePath: "/*" });

    expect(await screen.findByTestId("organizations-grid")).toBeInTheDocument();
  });
});
