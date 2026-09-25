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

  it("issues GET /ops/v1/organizations with a query string when list is called", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.list(withQuery("limit=10"));

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations?limit=10",
    });
  });

  it("forwards axios config overrides to http() for list", async () => {
    const { result } = renderHook(() => useOrganizationsApi());
    const signal = new AbortController().signal;

    await result.current.list(withQuery(""), { signal });

    expect(httpMock).toHaveBeenCalledWith({ method: "GET", url: "/ops/v1/organizations?", signal });
  });

  it("issues GET /ops/v1/organizations/{id} when get is called", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.get("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1",
    });
  });

  it("issues DELETE /ops/v1/organizations/{id} when deleteOrganization is called", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.deleteOrganization("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "DELETE",
      url: "/ops/v1/organizations/org-1",
    });
  });

  it("issues PUT /ops/v1/organizations/{id} with only the name field when editOrganization is called", async () => {
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

  it("issues GET /ops/v1/organizations/{id}/employees when listOrganizationEmployees is called", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.listOrganizationEmployees("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1/employees",
    });
  });

  it("issues GET /ops/v1/organizations/{id}/datasources when listOrganizationDataSources is called", async () => {
    const { result } = renderHook(() => useOrganizationsApi());

    await result.current.listOrganizationDataSources("org-1");

    expect(httpMock).toHaveBeenCalledWith({
      method: "GET",
      url: "/ops/v1/organizations/org-1/datasources",
    });
  });

  it("issues POST /ops/v1/organizations/{id}/datasources/{dsId}/force-reimport with body when forceReimportDatasource is called", async () => {
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
