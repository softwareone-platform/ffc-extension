import { renderHook } from "@testing-library/react";

import { http } from "@mpt-extension/sdk";

import { useEntitlementsApi } from "./useEntitlementsApi";

const httpMock = http as jest.MockedFunction<typeof http>;

describe("useEntitlementsApi", () => {
  beforeEach(() => {
    httpMock.mockResolvedValue({ data: undefined } as unknown as ReturnType<typeof http>);
  });

  it("lists entitlements using the provided query", async () => {
    const { result } = renderHook(() => useEntitlementsApi());

    await result.current.list({ toString: () => "limit=10" } as never);

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/entitlements?limit=10",
    });
  });

  it("fetches an entitlement by id", async () => {
    const { result } = renderHook(() => useEntitlementsApi());

    await result.current.get("ent-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/entitlements/ent-1",
    });
  });

  it("creates an entitlement when no id is provided", async () => {
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

  it("updates an entitlement when an id is provided", async () => {
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

  it("terminates an entitlement", async () => {
    const { result } = renderHook(() => useEntitlementsApi());

    await result.current.terminateEntitlement("ent-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "POST",
      url: "/ops/v1/entitlements/ent-1/terminate",
    });
  });

  it("deletes an entitlement", async () => {
    const { result } = renderHook(() => useEntitlementsApi());

    await result.current.deleteEntitlement("ent-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "DELETE",
      url: "/ops/v1/entitlements/ent-1",
    });
  });
});
