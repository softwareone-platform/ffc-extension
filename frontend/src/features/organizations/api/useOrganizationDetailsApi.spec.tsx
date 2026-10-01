import { renderHook, waitFor } from "@testing-library/react";

import { createQueryClientWrapper } from "~test-utils";

import { useOrganizationDetailsApi } from "./useOrganizationDetailsApi";
import type { useOrganizationsApi } from "./useOrganizationsApi";

type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;

const mockGet = jest.fn() as jest.MockedFunction<OrganizationsApi["get"]>;

jest.mock("./useOrganizationsApi", () => ({
  useOrganizationsApi: () => ({ get: mockGet }),
}));

describe("useOrganizationDetailsApi", () => {
  it("disables the query and does not call get when organizationId is undefined", () => {
    const { result } = renderHook(() => useOrganizationDetailsApi(undefined), {
      wrapper: createQueryClientWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGet).not.toHaveBeenCalled();
  });

  it("calls get with the organizationId and selects the response data when defined", async () => {
    const organization = { id: "org-1", name: "Acme" };
    mockGet.mockResolvedValueOnce({ data: organization } as unknown as Awaited<
      ReturnType<OrganizationsApi["get"]>
    >);

    const { result } = renderHook(() => useOrganizationDetailsApi("org-1"), {
      wrapper: createQueryClientWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith("org-1");
    expect(result.current.data).toBe(organization);
  });
});
