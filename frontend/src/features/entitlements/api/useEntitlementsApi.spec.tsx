import { renderHook } from "@testing-library/react";

import { http } from "@mpt-extension/sdk";

import { useEntitlementsApi } from "./useEntitlementsApi";

const httpMock = http as jest.MockedFunction<typeof http>;

describe("useEntitlementsApi", () => {
  beforeEach(() => {
    httpMock.mockResolvedValue({ data: undefined } as unknown as ReturnType<typeof http>);
  });

  it("issues GET /ops/v1/entitlements with a query string when list is called", async () => {
    const { result } = renderHook(() => useEntitlementsApi());

    await result.current.list({ toString: () => "limit=10" } as never);

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/entitlements?limit=10",
    });
  });

  it("issues GET /ops/v1/entitlements/{id} when get is called", async () => {
    const { result } = renderHook(() => useEntitlementsApi());

    await result.current.get("ent-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/entitlements/ent-1",
    });
  });

  it("issues POST /ops/v1/entitlements when save is called without an id (create)", async () => {
    const { result } = renderHook(() => useEntitlementsApi());
    const body = {
      name: "New",
      affiliate_external_id: "aff-ext",
      datasource_id: "ds-1",
    };

    await result.current.save(body);

    expect(httpMock).toHaveBeenCalledWith({
      method: "POST",
      url: "/ops/v1/entitlements",
      data: body,
    });
  });

  it("issues PUT /ops/v1/entitlements/{id} when save is called with an id (update)", async () => {
    const { result } = renderHook(() => useEntitlementsApi());
    const body = {
      id: "ent-1",
      name: "Updated",
      affiliate_external_id: "aff-ext",
      datasource_id: "ds-1",
    };

    await result.current.save(body as never);

    expect(httpMock).toHaveBeenCalledWith({
      method: "PUT",
      url: "/ops/v1/entitlements/ent-1",
      data: body,
    });
  });

  it("issues POST /ops/v1/entitlements/{id}/terminate when terminateEntitlement is called", async () => {
    const { result } = renderHook(() => useEntitlementsApi());

    await result.current.terminateEntitlement("ent-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "POST",
      url: "/ops/v1/entitlements/ent-1/terminate",
    });
  });

  it("issues DELETE /ops/v1/entitlements/{id} when deleteEntitlement is called", async () => {
    const { result } = renderHook(() => useEntitlementsApi());

    await result.current.deleteEntitlement("ent-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "DELETE",
      url: "/ops/v1/entitlements/ent-1",
    });
  });
});
