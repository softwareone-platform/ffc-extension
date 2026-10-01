import { act, renderHook, waitFor } from "@testing-library/react";

import { RqlQuery } from "@swo/rql-client";

import { createQueryClientWrapper, createTestQueryClient } from "~test-utils";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import { useReactQueryRqlGrid } from "./useReactQueryRqlGrid";

// Load-bearing: the hook imports `buildRqlQuery` at runtime; without the mock,
// Jest resolves the real @swo/design-system/grid module and OOMs.
jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);

function primeBuildRqlQuery(rql = "next-rql") {
  mockDesignSystemGrid.buildRqlQuery.mockReturnValue({
    toString: () => rql,
    clone() {
      return this;
    },
  } as unknown as RqlQuery<object>);
}

describe("useReactQueryRqlGrid", () => {
  const mockData = {
    data: [
      { id: "1", name: "Test Entity" },
      { id: "2", name: "Another Entity" },
    ],
    total: 2,
  };

  const mockQueryFn = jest.fn().mockResolvedValue(mockData);
  const mockBaseQueryKey = ["test-entities"];

  it("initializes with an empty data array and total 0", () => {
    const options = (query: RqlQuery<object>) => ({
      queryKey: ["test-entities", query.toString()],
      queryFn: mockQueryFn,
    });

    const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), {
      wrapper: createQueryClientWrapper(),
    });

    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.isLoading).toBe(false);
  });

  it("returns the query error after onConfigChange triggers a rejected fetch", async () => {
    const failure = new Error("boom");
    primeBuildRqlQuery();
    const options = (query: RqlQuery<object>) => ({
      queryKey: ["test-entities", query.toString()],
      queryFn: () => Promise.reject(failure),
    });

    const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), {
      wrapper: createQueryClientWrapper(),
    });
    await act(async () => {
      await result.current.onConfigChange(
        {} as unknown as Parameters<typeof result.current.onConfigChange>[0],
      );
    });

    await waitFor(() => expect(result.current.error).toBe(failure));
  });

  it("builds the RQL query from the supplied grid config", async () => {
    primeBuildRqlQuery();
    const options = (query: RqlQuery<object>) => ({
      queryKey: ["test-entities", query.toString()],
      queryFn: mockQueryFn,
    });
    const config = { columns: [], fields: [] };

    const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), {
      wrapper: createQueryClientWrapper(),
    });
    await act(async () => {
      await result.current.onConfigChange(
        config as unknown as Parameters<typeof result.current.onConfigChange>[0],
      );
    });

    expect(mockDesignSystemGrid.buildRqlQuery).toHaveBeenCalledWith(config);
  });

  it("refresh invalidates the scoped query key and silentRefresh invalidates the base query key", async () => {
    primeBuildRqlQuery("scoped-rql");
    const queryClient = createTestQueryClient();
    const invalidateSpy = jest.spyOn(queryClient, "invalidateQueries");
    const options = (query: RqlQuery<object>) => ({
      queryKey: ["test-entities", query.toString()],
      queryFn: mockQueryFn,
    });

    const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), {
      wrapper: createQueryClientWrapper(queryClient),
    });
    await act(async () => {
      await result.current.onConfigChange(
        {} as unknown as Parameters<typeof result.current.onConfigChange>[0],
      );
    });
    invalidateSpy.mockClear();

    await act(async () => {
      await result.current.refresh();
    });
    const refreshCall = invalidateSpy.mock.lastCall![0];
    await act(async () => {
      await result.current.silentRefresh();
    });
    const silentCall = invalidateSpy.mock.lastCall![0];

    expect(refreshCall).toEqual({ queryKey: ["test-entities", "scoped-rql"] });
    expect(silentCall).toEqual({ queryKey: mockBaseQueryKey });
  });
});
