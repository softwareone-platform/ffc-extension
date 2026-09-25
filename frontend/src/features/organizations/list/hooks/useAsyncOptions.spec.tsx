import { renderHook } from "@testing-library/react";

import type { useOrganizationsApi } from "~organizations/api";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";
import {
  mockReactQueryRqlGridModule,
  mockUseReactQueryRqlGrid,
} from "~test-utils/mocks/sharedGridHooks";

import { useAsyncOptions } from "./useAsyncOptions";

type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;

const mockList = jest.fn() as jest.MockedFunction<OrganizationsApi["list"]>;

jest.mock("~organizations/api", () => ({
  useOrganizationsApi: () => ({ list: mockList }),
}));

jest.mock("~shared/hooks/useReactQueryRqlGrid", () => mockReactQueryRqlGridModule);

describe("useAsyncOptions (organizations list)", () => {
  it("initializes useReactQueryRqlGrid with the Organizations base query key", () => {
    renderHook(() => useAsyncOptions());

    expect(mockUseReactQueryRqlGrid).toHaveBeenCalledWith(["Organizations"], expect.any(Function));
  });

  it("builds query options that add the query string to the queryKey and delegate to list()", () => {
    renderHook(() => useAsyncOptions());
    const optionsFactory = mockUseReactQueryRqlGrid.mock.lastCall![1];
    const query = { toString: () => "limit=25" };

    const options = optionsFactory(query);
    options.queryFn();

    expect(options.queryKey).toEqual(["Organizations", "limit=25"]);
    expect(mockList).toHaveBeenCalledWith(query);
  });

  it("wires mapAxiosResponseDataList as the select transform", () => {
    renderHook(() => useAsyncOptions());
    const optionsFactory = mockUseReactQueryRqlGrid.mock.lastCall![1];

    const options = optionsFactory({ toString: () => "rql" });

    expect(options.select).toBe(mapAxiosResponseDataList);
  });
});
