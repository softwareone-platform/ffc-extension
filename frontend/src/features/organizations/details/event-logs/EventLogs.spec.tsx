import type { ComponentProps } from "react";

import { screen } from "@testing-library/react";

import { renderWithOrganizationRoute, renderWithRouter } from "~test-utils";

import { OrganizationLogsDetails } from "./EventLogs";
import type { EventLogsGrid } from "./EventLogsGrid";

jest.mock("./EventLogsGrid", () => ({
  EventLogsGrid: ({ organizationId }: ComponentProps<typeof EventLogsGrid>) => (
    <div data-testid="event-logs-grid">{organizationId}</div>
  ),
}));

describe("OrganizationLogsDetails", () => {
  it("renders the event logs grid for the organization from the route", () => {
    renderWithOrganizationRoute(<OrganizationLogsDetails />, { id: "org-123" });

    expect(screen.getByTestId("event-logs-grid")).toHaveTextContent("org-123");
  });

  it("does not render the grid when the organizationId route param is missing", () => {
    renderWithRouter(<OrganizationLogsDetails />, {
      initialUrl: "/organizations",
      routePath: "/organizations",
    });

    expect(screen.queryByTestId("event-logs-grid")).not.toBeInTheDocument();
  });
});
