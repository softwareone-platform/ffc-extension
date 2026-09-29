import type { ComponentProps } from "react";

import { screen } from "@testing-library/react";

import { renderWithOrganizationRoute, renderWithRouter } from "~test-utils";

import { OrganizationDataSources } from "./DataSources";
import { DataSourcesGrid } from "./DataSourcesGrid";

jest.mock("./DataSourcesGrid", () => ({
  DataSourcesGrid: ({ organizationId }: ComponentProps<typeof DataSourcesGrid>) => (
    <div data-testid="data-sources-grid">{organizationId}</div>
  ),
}));

describe("OrganizationDataSources route component", () => {
  it("renders DataSourcesGrid with organizationId from route params", () => {
    renderWithOrganizationRoute(<OrganizationDataSources />, { id: "org-123" });

    expect(screen.getByTestId("data-sources-grid")).toHaveTextContent("org-123");
  });

  it("returns null when the organizationId route param is missing", () => {
    renderWithRouter(<OrganizationDataSources />, {
      initialUrl: "/organizations",
      routePath: "/organizations",
    });

    expect(screen.queryByTestId("data-sources-grid")).not.toBeInTheDocument();
  });
});
