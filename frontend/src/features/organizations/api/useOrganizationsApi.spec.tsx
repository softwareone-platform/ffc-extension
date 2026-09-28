import { renderHook } from "@testing-library/react";

import { http } from "@mpt-extension/sdk";

import { useOrganizationsApi } from "./useOrganizationsApi";

const httpMock = http as jest.MockedFunction<typeof http>;

function withQuery(str = "") {
  return { toString: () => str } as unknown as Parameters<
    ReturnType<typeof useOrganizationsApi>["list"]
  >[0];
}

describe("useOrganizationsApi", () => {
  beforeEach(() => {
    httpMock.mockResolvedValue({ data: undefined } as unknown as ReturnType<typeof http>);
  });

  it("lists organizations using the provided query", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.list(withQuery("limit=10"));

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations?limit=10",
    });
  });

  it("passes request options through when listing organizations", async () => {
    const { result } = renderHook(() => useOrganizationsApi());
    const signal = new AbortController().signal;

    await result.current.list(withQuery(""), { signal });

    expect(httpMock).toHaveBeenCalledWith({ method: "GET", url: "/ops/v1/organizations?", signal });
  });

  it("fetches an organization by id", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.get("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1",
    });
  });

  it("deletes an organization", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.deleteOrganization("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "DELETE",
      url: "/ops/v1/organizations/org-1",
    });
  });

  it("updates only the organization's name", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.editOrganization("org-1", {
      name: "Acme",
      operations_external_id: "ignored",
      currency: "USD",
    });

    expect(httpMock).toHaveBeenCalledWith({
      method: "PUT",
      url: "/ops/v1/organizations/org-1",
      data: { name: "Acme" },
    });
  });

  it("lists employees for an organization", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.listOrganizationEmployees("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1/employees",
    });
  });

  it("lists data sources for an organization", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.listOrganizationDataSources("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1/datasources",
    });
  });

  it("requests a data-source reimport with the provided payload", async () => {
    const { result } = renderHook(() => useOrganizationsApi());
    const body = { last_import_at: "2026-03-15" };

    await result.current.forceReimportDatasource("org-1", "ds-1", body);

    expect(httpMock).toHaveBeenCalledWith({
      method: "POST",
      url: "/ops/v1/organizations/org-1/datasources/ds-1/force-reimport",
      data: body,
    });
  });
});
