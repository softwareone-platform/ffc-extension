import { renderWithRouter } from "~test-utils";

import type { AccountType } from "~api/ffc-api-model";
import { mockUserRoleModule, mockUseUserRole } from "~test-utils/mocks/userRole";

import {
  mockEntitlementDetailsHeader,
  mockHeader,
  mockOrganizationDetailsHeader,
} from "./MainLayout.spec.mocks";

import { MainLayout } from "./MainLayout";

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);


function renderAt(initialUrl: string) {
  return renderWithRouter(<MainLayout />, { initialUrl, routePath: "/*" });
}

describe("MainLayout", () => {
  it("renders the OrganizationDetailsHeader when on an organization detail URL", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });

    renderAt("/organizations/org-1");

    expect(mockOrganizationDetailsHeader).toHaveBeenCalledWith({
      organizationId: "org-1",
      backUrl: "/organizations",
    });
  });

  it("renders the EntitlementDetailsHeader when on an entitlement detail URL", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });

    renderAt("/entitlements/ent-1");

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

    renderAt("/");

    const items = mockHeader.mock.lastCall![0].items!;
    expect(items.map((i) => i.path)).toEqual(expectedPaths);
  });

  it("treats a missing role as affiliate for nav filtering", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: undefined });

    renderAt("/");

    const items = mockHeader.mock.lastCall![0].items!;
    expect(items.map((i) => i.path)).toEqual(["/entitlements"]);
  });
});
