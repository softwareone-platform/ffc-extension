import { screen, waitFor } from "@testing-library/react";

import { renderWithRouter } from "~test-utils";

import { mockRouteGuard } from "./Organizations.spec.mocks";

import { Organizations } from "./Organizations";

function renderOrganizations(initialUrl: string) {
  return renderWithRouter(<Organizations />, {
    initialUrl,
    routePath: "/organizations/*",
  });
}

describe("Organizations router", () => {
  it("guards the route tree with the admin and operations roles", async () => {
    renderOrganizations("/organizations");

    await waitFor(() =>
      expect(mockRouteGuard).toHaveBeenCalledWith({ allowedRoles: ["admin", "operations"] }),
    );
  });

  it("renders OrganizationsGrid at the index route", async () => {
    renderOrganizations("/organizations");

    expect(await screen.findByTestId("organizations-grid")).toBeInTheDocument();
  });

  it("renders the details shell and general tab at the bare detail route", async () => {
    renderOrganizations("/organizations/org-1");

    expect(await screen.findByTestId("details-content")).toBeInTheDocument();
    expect(await screen.findByTestId("general")).toBeInTheDocument();
  });

  it.each([
    ["/organizations/org-1/general", "general"],
    ["/organizations/org-1/data-sources", "data-sources"],
    ["/organizations/org-1/users", "users"],
    ["/organizations/org-1/events", "events"],
  ] as const)("renders %s inside the details shell", async (url, testId) => {
    renderOrganizations(url);

    expect(await screen.findByTestId("details-content")).toBeInTheDocument();
    expect(await screen.findByTestId(testId)).toBeInTheDocument();
  });
});
