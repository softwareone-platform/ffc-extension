import { renderHook } from "@testing-library/react";

import type { useOrganizationsApi } from "~features/organizations/api";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";
import { mockReactQueryRqlGridModule, mockUseReactQueryRqlGrid } from "~test-utils/mocks/gridHooks";

import { useAsyncOptions } from "./useAsyncOptions";

type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;

const mockListOrganizationLogs = jest.fn() as jest.MockedFunction<
  OrganizationsApi["listOrganizationLogs"]
>;

jest.mock("~features/organizations/api", () => ({
  useOrganizationsApi: () => ({ listOrganizationLogs: mockListOrganizationLogs }),
}));

jest.mock("~shared/hooks/useReactQueryRqlGrid", () => mockReactQueryRqlGridModule);

function getLatestOptionsFactory() {
  return mockUseReactQueryRqlGrid.mock.lastCall![1];
}

describe("useAsyncOptions (organization event logs)", () => {
  it("initializes useReactQueryRqlGrid with an organization-scoped logs query key", () => {
    renderHook(() => useAsyncOptions("org-123"));

    expect(mockUseReactQueryRqlGrid).toHaveBeenCalledWith(
      ["OrganizationLogs", "org-123"],
      expect.any(Function),
    );
  });

  it("builds query options that list the organization's logs", () => {
    renderHook(() => useAsyncOptions("org-123"));
    const query = { toString: () => "rql-string" };

    const options = getLatestOptionsFactory()(query);
    options.queryFn();

    expect(options.queryKey).toEqual([["OrganizationLogs", "org-123"], "rql-string", "org-123"]);
    expect(mockListOrganizationLogs).toHaveBeenCalledWith("org-123", query);
  });

  it("wires mapAxiosResponseDataList as the select transform", () => {
    renderHook(() => useAsyncOptions("org-123"));

    const options = getLatestOptionsFactory()({ toString: () => "rql" });

    expect(options.select).toBe(mapAxiosResponseDataList);
  });
});
