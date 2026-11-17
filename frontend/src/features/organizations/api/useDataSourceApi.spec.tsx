import { renderHook, waitFor } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import type { useEntityApi } from "~shared/hooks/useEntityApi";
import { createQueryClientWrapper } from "~test-utils";

import { useDataSourceApi } from "./useDataSourceApi";

type DataSourceEntityApi = ReturnType<typeof useEntityApi<DatasourceDetailRead>>;

const mockGet = jest.fn() as jest.MockedFunction<DataSourceEntityApi["get"]>;
const mockUseEntityApi = jest.fn() as jest.MockedFunction<(rootPath: string) => void>;

jest.mock("~shared/hooks/useEntityApi", () => ({
  useEntityApi: (rootPath: string) => {
    mockUseEntityApi(rootPath);
    return { get: mockGet };
  },
}));

function renderDataSourceApi(organizationId: string | undefined, dataSourceId: string | undefined) {
  return renderHook(() => useDataSourceApi(organizationId, dataSourceId), {
    wrapper: createQueryClientWrapper(),
  });
}

describe("useDataSourceApi", () => {
  it.each([
    ["organizationId", undefined, "ds-1"],
    ["dataSourceId", "org-1", undefined],
  ])("does not fetch when %s is missing", (_, organizationId, dataSourceId) => {
    const { result } = renderDataSourceApi(organizationId, dataSourceId);

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGet).not.toHaveBeenCalled();
  });

  it("fetches the data source by id from the organization's datasources endpoint", async () => {
    const dataSource = { id: "ds-1", name: "AWS Prod" } as DatasourceDetailRead;
    mockGet.mockResolvedValueOnce({ data: dataSource } as Awaited<
      ReturnType<DataSourceEntityApi["get"]>
    >);

    const { result } = renderDataSourceApi("org-1", "ds-1");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockUseEntityApi).toHaveBeenCalledWith("/ops/v1/organizations/org-1/datasources");
    expect(mockGet).toHaveBeenCalledWith("ds-1");
    expect(result.current.data).toBe(dataSource);
  });
});
