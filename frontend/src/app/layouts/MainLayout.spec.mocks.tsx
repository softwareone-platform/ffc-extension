import type { ComponentProps, ReactNode } from "react";

import type { PageShell } from "~shared/components/page-shell";

export type MockHeaderProps = ComponentProps<typeof PageShell.Header>;

export const mockHeader = jest.fn() as jest.MockedFunction<(props: MockHeaderProps) => void>;
export const mockOrganizationDetailsHeader = jest.fn() as jest.MockedFunction<
  (props: { organizationId: string; backUrl: string }) => void
>;
export const mockEntitlementDetailsHeader = jest.fn() as jest.MockedFunction<
  (props: { entitlementId: string; backUrl: string }) => void
>;

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

