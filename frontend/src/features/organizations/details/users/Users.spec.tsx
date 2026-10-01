import { screen } from "@testing-library/react";

import { renderWithOrganizationRoute, renderWithRouter } from "~test-utils";

import { OrganizationUsers } from "./Users";
import type { UsersGrid } from "./UsersGrid";

type MockUsersGridProps = React.ComponentProps<typeof UsersGrid>;

jest.mock("./UsersGrid", () => ({
  UsersGrid: ({ organizationId }: MockUsersGridProps) => (
    <div data-testid="users-grid">{organizationId}</div>
  ),
}));

describe("OrganizationUsers route component", () => {
  it("renders UsersGrid with organizationId from route params", () => {
    renderWithOrganizationRoute(<OrganizationUsers />, { id: "org-123" });

    expect(screen.getByTestId("users-grid")).toHaveTextContent("org-123");
  });

  it("returns nothing when the organizationId route param is missing", () => {
    renderWithRouter(<OrganizationUsers />, {
      initialUrl: "/organizations",
      routePath: "/organizations",
    });

    expect(screen.queryByTestId("users-grid")).not.toBeInTheDocument();
  });
});
