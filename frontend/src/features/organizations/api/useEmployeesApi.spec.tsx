import { renderHook } from "@testing-library/react";

import { http } from "@mpt-extension/sdk";

import { useEmployeesApi } from "./useEmployeesApi";

const httpMock = http as jest.MockedFunction<typeof http>;

describe("useEmployeesApi", () => {
  beforeEach(() => {
    httpMock.mockResolvedValue({ data: undefined } as unknown as ReturnType<typeof http>);
  });

  it("issues GET /ops/v1/organizations/{id}/employees without a query string when list is called with no query", async () => {
    const { result } = renderHook(() => useEmployeesApi());

    await result.current.list("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1/employees",
    });
  });

  it("forwards axios config overrides to http() for list", async () => {
    const { result } = renderHook(() => useEmployeesApi());
    const signal = new AbortController().signal;

    await result.current.list("org-1", undefined, { signal });

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1/employees",
      signal,
    });
  });

  it("issues POST /ops/v1/organizations/{id}/add-admin with the form body plus admin note when addAdmin is called", async () => {
    const { result } = renderHook(() => useEmployeesApi());

    await result.current.addAdmin("org-1", { email: "user@example.com", display_name: "User" });

    expect(httpMock).toHaveBeenCalledWith({
      method: "POST",
      url: "/ops/v1/organizations/org-1/add-admin",
      data: {
        email: "user@example.com",
        display_name: "User",
        notes: "Add user as admin",
      },
    });
  });

  it("issues POST /ops/v1/organizations/{id}/employees/{empId}/make-admin when promoteToAdmin is called", async () => {
    const { result } = renderHook(() => useEmployeesApi());

    await result.current.promoteToAdmin("org-1", "emp-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "POST",
      url: "/ops/v1/organizations/org-1/employees/emp-1/make-admin",
    });
  });
});
