import { screen } from "@testing-library/react";

import { renderWithRouter } from "~test-utils";

import { OrganizationDataSources } from "./DataSources";

jest.mock("./DataSourcesGrid", () => ({
  DataSourcesGrid: ({ organizationId }: { organizationId: string }) => (
    <div data-testid="data-sources-grid">{organizationId}</div>
  ),
}));

describe("OrganizationDataSources", () => {
  it("renders DataSourcesGrid with organizationId from route params", () => {
    renderWithRouter(<OrganizationDataSources />, {
      initialUrl: "/organizations/org-123",
      routePath: "/organizations/:organizationId",
    });

    expect(screen.getByTestId("data-sources-grid")).toHaveTextContent("org-123");
  });

  it("renders nothing when organizationId is missing", () => {
    renderWithRouter(<OrganizationDataSources />, {
      initialUrl: "/organizations",
      routePath: "/organizations",
    });

    expect(screen.queryByTestId("data-sources-grid")).not.toBeInTheDocument();
  });
});
