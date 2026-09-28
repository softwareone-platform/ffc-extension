import type { ComponentProps } from "react";

import type { EntitlementDetailsHeader } from "~features/entitlements/components/EntitlementDetailsHeader";
import type { OrganizationDetailsHeader } from "~features/organizations/components/OrganizationDetailsHeader";
import type { PageShell } from "~shared/components/page-shell";
import { mockUserRoleModule } from "~test-utils/mocks/userRole";

export { mockUseUserRole } from "~test-utils/mocks/userRole";

export type MockHeaderProps = ComponentProps<typeof PageShell.Header>;
type MockPageShellProps = ComponentProps<typeof PageShell>;
type MockPageShellContentProps = ComponentProps<typeof PageShell.Content>;
type MockOrganizationDetailsHeaderProps = ComponentProps<typeof OrganizationDetailsHeader>;
type MockEntitlementDetailsHeaderProps = ComponentProps<typeof EntitlementDetailsHeader>;

export const mockHeader = jest.fn() as jest.MockedFunction<(props: MockHeaderProps) => void>;
export const mockOrganizationDetailsHeader = jest.fn() as jest.MockedFunction<
  (props: MockOrganizationDetailsHeaderProps) => void
>;
export const mockEntitlementDetailsHeader = jest.fn() as jest.MockedFunction<
  (props: MockEntitlementDetailsHeaderProps) => void
>;

jest.mock("~shared/components/page-shell", () => ({
  PageShell: Object.assign(
    ({ children }: MockPageShellProps) => <div data-testid="page-shell">{children}</div>,
    {
      Header: (props: MockHeaderProps) => {
        mockHeader(props);
        return <header data-testid="page-shell-header" />;
      },
      Content: ({ children }: MockPageShellContentProps) => (
        <main data-testid="page-shell-content">{children}</main>
      ),
    },
  ),
}));

jest.mock("~features/organizations/components/OrganizationDetailsHeader", () => ({
  OrganizationDetailsHeader: (props: MockOrganizationDetailsHeaderProps) => {
    mockOrganizationDetailsHeader(props);
    return <div data-testid="organization-header" />;
  },
}));

jest.mock("~features/entitlements/components/EntitlementDetailsHeader", () => ({
  EntitlementDetailsHeader: (props: MockEntitlementDetailsHeaderProps) => {
    mockEntitlementDetailsHeader(props);
    return <div data-testid="entitlement-header" />;
  },
}));

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);
