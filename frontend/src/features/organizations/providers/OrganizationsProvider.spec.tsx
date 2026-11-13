import { renderHook } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";

import { OrganizationsProvider, useOrganizationContext } from "./OrganizationsProvider";

describe("OrganizationsProvider", () => {
  it("makes the organization available to consumers via useOrganizationContext", () => {
    const organization = { id: "org-1", name: "Acme" } as OrganizationRead;
    const { result } = renderHook(() => useOrganizationContext(), {
      wrapper: ({ children }) => (
        <OrganizationsProvider organization={organization}>{children}</OrganizationsProvider>
      ),
    });

    expect(result.current).toBe(organization);
  });

  it("returns the context default (an empty organization stand-in) when used outside a provider", () => {
    const { result } = renderHook(() => useOrganizationContext());

    expect(result.current).toEqual({});
  });

  it("returns undefined while the provider has no organization loaded yet", () => {
    const { result } = renderHook(() => useOrganizationContext(), {
      wrapper: ({ children }) => (
        <OrganizationsProvider organization={undefined as unknown as OrganizationRead}>
          {children}
        </OrganizationsProvider>
      ),
    });

    expect(result.current).toBeUndefined();
  });
});
