import { MemoryRouter, Route, Routes } from "react-router-dom";

import { render, screen } from "@testing-library/react";

import { OrganizationDataSources } from "./DataSources";

jest.mock("./DataSourcesGrid", () => ({
  DataSourcesGrid: ({ organizationId }: { organizationId: string }) => (
    <div data-testid="data-sources-grid">{organizationId}</div>
  ),
}));

function renderAt(url: string, routePath: string) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <Routes>
        <Route path={routePath} element={<OrganizationDataSources />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OrganizationDataSources", () => {
  it("renders DataSourcesGrid with organizationId from route params", () => {
    renderAt("/organizations/org-123", "/organizations/:organizationId");

    expect(screen.getByTestId("data-sources-grid")).toHaveTextContent("org-123");
  });

  it("renders nothing when organizationId is missing", () => {
    renderAt("/organizations", "/organizations");

    expect(screen.queryByTestId("data-sources-grid")).not.toBeInTheDocument();
  });
});
