import type { AccountType } from "~api/ffc-api-model";
import { renderWithRouter } from "~test-utils";

import {
  mockDataSourceDetailsHeader,
  mockEntitlementDetailsHeader,
  mockHeader,
  mockOrganizationDetailsHeader,
  mockUseUserRole,
} from "./MainLayout.spec.mocks";

import { MainLayout } from "./MainLayout";

describe("MainLayout", () => {
  it("renders the organization details header on an organization details page", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });

    renderWithRouter(<MainLayout />, {
      initialUrl: "/organizations/org-1",
      routePath: "/*",
    });

    expect(mockOrganizationDetailsHeader).toHaveBeenCalledWith({
      organizationId: "org-1",
      backUrl: "/organizations",
    });
  });

  it("renders the data source details header instead of the organization one on a data source page", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });

    renderWithRouter(<MainLayout />, {
      initialUrl: "/organizations/org-1/data-sources/ds-1/details",
      routePath: "/*",
    });

    expect(mockDataSourceDetailsHeader).toHaveBeenCalledWith({
      organizationId: "org-1",
      dataSourceId: "ds-1",
      backUrl: "/organizations/org-1/data-sources",
    });
    expect(mockOrganizationDetailsHeader).not.toHaveBeenCalled();
  });

  it("renders the entitlement details header on an entitlement details page", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });

    renderWithRouter(<MainLayout />, {
      initialUrl: "/entitlements/ent-1",
      routePath: "/*",
    });

    expect(mockEntitlementDetailsHeader).toHaveBeenCalledWith({
      entitlementId: "ent-1",
      backUrl: "/entitlements",
    });
  });

  it.each<[AccountType, string[]]>([
    ["admin", ["/organizations", "/entitlements"]],
    ["operations", ["/organizations", "/entitlements"]],
    ["affiliate", ["/entitlements"]],
  ])("filters nav items by role '%s' to %j", (role, expectedPaths) => {
    mockUseUserRole.mockReturnValue({ user: null, role });

    renderWithRouter(<MainLayout />, {
      initialUrl: "/",
      routePath: "/*",
    });

    const items = mockHeader.mock.lastCall![0].items!;
    expect(items.map((i) => i.path)).toEqual(expectedPaths);
  });

  it("treats a missing role as affiliate for nav filtering", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: undefined });

    renderWithRouter(<MainLayout />, {
      initialUrl: "/",
      routePath: "/*",
    });

    const items = mockHeader.mock.lastCall![0].items!;
    expect(items.map((i) => i.path)).toEqual(["/entitlements"]);
  });
});
