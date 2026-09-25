import { renderHook } from "@testing-library/react";

import { http } from "@mpt-extension/sdk";

import { useAccountsApi } from "./useAccountsApi";

const httpMock = http as jest.MockedFunction<typeof http>;

function withQuery(str = "") {
  return { toString: () => str } as unknown as Parameters<
    ReturnType<typeof useAccountsApi>["list"]
  >[0];
}

describe("useAccountsApi", () => {
  beforeEach(() => {
    httpMock.mockResolvedValue({ data: undefined } as unknown as ReturnType<typeof http>);
  });

  it("issues GET /ops/v1/accounts with a query string when list is called", async () => {
    const { result } = renderHook(() => useAccountsApi());

    await result.current.list(withQuery("limit=10"));

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/accounts?limit=10",
    });
  });

  it("forwards axios config overrides to http() for list", async () => {
    const { result } = renderHook(() => useAccountsApi());
    const signal = new AbortController().signal;

    await result.current.list(withQuery(""), { signal });

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/accounts?",
      signal,
    });
  });
});
