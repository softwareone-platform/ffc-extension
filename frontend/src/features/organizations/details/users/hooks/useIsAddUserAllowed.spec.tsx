import { renderHook } from "@testing-library/react";

import type { AccountType, OrganizationRead, OrganizationStatus } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~features/organizations/api/useOrganizationDetailsApi";
import type { useUserRole } from "~shared/hooks/useUserRole";

import { useIsUserAddAllowed } from "./useIsAddUserAllowed";

type ApiResult = ReturnType<typeof useOrganizationDetailsApi>;

const mockUseUserRole = jest.fn() as jest.MockedFunction<typeof useUserRole>;
const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;

jest.mock("~shared/hooks/useUserRole", () => ({
  useUserRole: () => mockUseUserRole(),
}));

jest.mock("~features/organizations/api/useOrganizationDetailsApi", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

function primeOrg(status: OrganizationStatus | undefined) {
  mockUseOrganizationDetailsApi.mockReturnValue({
    data: status ? ({ status } as OrganizationRead) : undefined,
  } as unknown as ApiResult);
}

describe("useIsUserAddAllowed", () => {
  it("allows add-user for admin role on an active organization", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
    primeOrg("active");

    const { result } = renderHook(() => useIsUserAddAllowed("org-1"));

    expect(result.current.isAddUserAllowed).toBe(true);
  });

  it.each<AccountType>(["operations", "affiliate"])(
    "denies add-user for non-admin role '%s'",
    (role) => {
      mockUseUserRole.mockReturnValue({ user: null, role });
      primeOrg("active");

      const { result } = renderHook(() => useIsUserAddAllowed("org-1"));

      expect(result.current.isAddUserAllowed).toBeFalsy();
    },
  );

  it.each<OrganizationStatus>(["terminated", "deleted"])(
    "denies add-user for status '%s' even for an admin",
    (status) => {
      mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
      primeOrg(status);

      const { result } = renderHook(() => useIsUserAddAllowed("org-1"));

      expect(result.current.isAddUserAllowed).toBeFalsy();
    },
  );

  it("denies add-user when the organization has not loaded yet", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
    primeOrg(undefined);

    const { result } = renderHook(() => useIsUserAddAllowed("org-1"));

    expect(result.current.isAddUserAllowed).toBeFalsy();
  });

  it("denies add-user when the role is missing", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: undefined });
    primeOrg("active");

    const { result } = renderHook(() => useIsUserAddAllowed("org-1"));

    expect(result.current.isAddUserAllowed).toBeFalsy();
  });
});
