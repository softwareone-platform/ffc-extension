import { renderHook } from "@testing-library/react";

import { http } from "@mpt-extension/sdk";

import { useEmployeesApi } from "./useEmployeesApi";

const httpMock = http as jest.MockedFunction<typeof http>;

describe("useEmployeesApi", () => {
  beforeEach(() => {
    httpMock.mockResolvedValue({ data: undefined } as unknown as ReturnType<typeof http>);
  });

  it("lists an organization's employees without query parameters when no query is provided", async () => {
    const { result } = renderHook(() => useEmployeesApi());

    await result.current.list("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1/employees",
    });
  });

  it("passes request options through when listing employees", async () => {
    const { result } = renderHook(() => useEmployeesApi());
    const signal = new AbortController().signal;

    await result.current.list("org-1", undefined, { signal });

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1/employees",
      signal,
    });
  });

  it("adds an organization admin and includes the default admin note", async () => {
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

  it("promotes an employee to organization admin", async () => {
    const { result } = renderHook(() => useEmployeesApi());

    await result.current.promoteToAdmin("org-1", "emp-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "POST",
      url: "/ops/v1/organizations/org-1/employees/emp-1/make-admin",
    });
  });
});
