import { PropsWithChildren } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";

import { RqlQuery } from "@swo/rql-client";

import { useReactQueryRqlGrid } from "./useReactQueryRqlGrid";

jest.mock("@swo/grid", () => ({
  ...jest.requireActual("@swo/grid"),
  buildRqlQuery: jest.fn(),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  function TestComponent({ children }: PropsWithChildren) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }

  return TestComponent;
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

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should initialize with empty data array and total 0", () => {
    const options = (query: RqlQuery<object>) => ({
      queryKey: ["test-entities", query.toString()],
      queryFn: mockQueryFn,
    });

    const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), {
      wrapper: createWrapper(),
    });

    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.isLoading).toBe(false);
  });
});
