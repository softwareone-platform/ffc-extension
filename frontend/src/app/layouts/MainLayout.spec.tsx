import type { ComponentProps, ReactNode } from "react";

import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import type { AccountType } from "~api/ffc-api-model";
import type { PageShell } from "~shared/components/page-shell";
import { mockUserRoleModule, mockUseUserRole } from "~test-utils/mocks/userRole";

import { MainLayout } from "./MainLayout";

type MockHeaderProps = ComponentProps<typeof PageShell.Header>;

const mockHeader = jest.fn() as jest.MockedFunction<(props: MockHeaderProps) => void>;
const mockOrganizationDetailsHeader = jest.fn() as jest.MockedFunction<
  (props: { organizationId: string; backUrl: string }) => void
>;
const mockEntitlementDetailsHeader = jest.fn() as jest.MockedFunction<
  (props: { entitlementId: string; backUrl: string }) => void
>;

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

jest.mock("~shared/components/page-shell", () => ({
  PageShell: Object.assign(
    ({ children }: { children?: ReactNode }) => <div data-testid="page-shell">{children}</div>,
    {
      Header: (props: MockHeaderProps) => {
        mockHeader(props);
        return <header data-testid="page-shell-header" />;
      },
      Content: ({ children }: { children?: ReactNode }) => (
        <main data-testid="page-shell-content">{children}</main>
      ),
    },
  ),
}));

jest.mock("~features/organizations/components/OrganizationDetailsHeader", () => ({
  OrganizationDetailsHeader: (props: { organizationId: string; backUrl: string }) => {
    mockOrganizationDetailsHeader(props);
    return <div data-testid="organization-header" />;
  },
}));

jest.mock("~features/entitlements/components/EntitlementDetailsHeader", () => ({
  EntitlementDetailsHeader: (props: { entitlementId: string; backUrl: string }) => {
    mockEntitlementDetailsHeader(props);
    return <div data-testid="entitlement-header" />;
  },
}));

function renderAt(initialUrl: string) {
  return render(
    <MemoryRouter initialEntries={[initialUrl]}>
      <Routes>
        <Route path="*" element={<MainLayout />} />
      </Routes>
    </MemoryRouter>,
  );
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
