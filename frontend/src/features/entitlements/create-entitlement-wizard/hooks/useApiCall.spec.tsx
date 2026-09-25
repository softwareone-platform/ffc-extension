import { act, renderHook } from "@testing-library/react";

import type { Column } from "@swo/design-system/list";

import type { Account } from "~features/entitlements/api/model";
import type { useAccountsApi } from "~features/entitlements/api/useAccountsApi";
import type { useUserRole } from "~shared/hooks/useUserRole";
import { makeAccount } from "~test-utils";
import { mockUserRoleModule, mockUseUserRole } from "~test-utils/mocks/userRole";

import { useApiCall } from "./useApiCall";

type AccountsApi = ReturnType<typeof useAccountsApi>;

const mockList = jest.fn() as jest.MockedFunction<AccountsApi["list"]>;

jest.mock("~features/entitlements/api/useAccountsApi", () => ({
  useAccountsApi: () => ({ list: mockList }),
}));

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

const columns: Column<Account>[] = [
  { name: "id", filterable: true, hide: true },
  { name: "name", filterable: true },
];

function primeAffiliate(account: Account) {
  mockUseUserRole.mockReturnValue({
    user: { account } as unknown as NonNullable<ReturnType<typeof useUserRole>["user"]>,
    role: "affiliate",
  });
}

function primeOperations() {
  mockUseUserRole.mockReturnValue({ user: null, role: "operations" });
}

describe("useApiCall", () => {
  it("returns the affiliate's own account without calling list() when role is 'affiliate'", async () => {
    const own = makeAccount({ id: "own-1", name: "Me" });
    primeAffiliate(own);
    const { result } = renderHook(() => useApiCall(columns));

    let response: { data: Account[]; total: number } | undefined;
    await act(async () => {
      response = await result.current("", 0, 20);
    });

    expect(response).toEqual({ data: [own], total: 1 });
    expect(mockList).not.toHaveBeenCalled();
  });

  it("calls the accounts list for non-affiliate roles and returns mapped data", async () => {
    primeOperations();
    const account = makeAccount({ id: "acc-1", name: "One" });
    mockList.mockResolvedValueOnce({
      data: { items: [account], total: 1 },
    } as unknown as Awaited<ReturnType<AccountsApi["list"]>>);
    const { result } = renderHook(() => useApiCall(columns));

    let response: { data: Account[]; total: number } | undefined;
    await act(async () => {
      response = await result.current("name==x", 0, 20);
    });

    expect(mockList).toHaveBeenCalledTimes(1);
    expect(response).toEqual({ data: [account], total: 1 });
  });
});
