import { renderHook } from "@testing-library/react";

import { RqlQuery } from "@swo/rql-client";

import { createQueryClientWrapper } from "~test-utils";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import { useReactQueryRqlGrid } from "./useReactQueryRqlGrid";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);

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

  it("should initialize with empty data array and total 0", () => {
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
});
