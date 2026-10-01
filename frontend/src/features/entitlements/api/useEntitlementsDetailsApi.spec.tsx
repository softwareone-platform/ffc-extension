import { renderHook, waitFor } from "@testing-library/react";

import { createQueryClientWrapper } from "~test-utils";

import type { useEntitlementsApi } from "./useEntitlementsApi";
import { useEntitlementsDetailsApi } from "./useEntitlementsDetailsApi";

type EntitlementsApi = ReturnType<typeof useEntitlementsApi>;

const mockGet = jest.fn() as jest.MockedFunction<EntitlementsApi["get"]>;

jest.mock("./useEntitlementsApi", () => ({
  useEntitlementsApi: () => ({ get: mockGet }),
}));

describe("useEntitlementsDetailsApi", () => {
  it("disables the query and does not call get when entitlementId is undefined", () => {
    const { result } = renderHook(() => useEntitlementsDetailsApi(undefined), {
      wrapper: createQueryClientWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGet).not.toHaveBeenCalled();
  });

  it("calls get with the entitlementId and selects the response data when defined", async () => {
    const entitlement = { id: "ent-1", name: "One" };
    mockGet.mockResolvedValueOnce({ data: entitlement } as unknown as Awaited<
      ReturnType<EntitlementsApi["get"]>
    >);

    const { result } = renderHook(() => useEntitlementsDetailsApi("ent-1"), {
      wrapper: createQueryClientWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith("ent-1");
    expect(result.current.data).toBe(entitlement);
  });
});
