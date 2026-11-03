import { screen } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import type { useDataSourceApi } from "~features/organizations/api/useDataSourceApi";
import { makeDatasourceDetail, renderWithOrganizationRoute } from "~test-utils";

import { DataSourceDetails } from "./DataSourceDetails";

type UseDataSourceApiResult = ReturnType<typeof useDataSourceApi>;
type MockPropertiesProps = { entity: DatasourceDetailRead };

const mockUseDataSourceApi = jest.fn() as jest.MockedFunction<typeof useDataSourceApi>;

jest.mock("~features/organizations/api/useDataSourceApi", () => ({
  useDataSourceApi: (...args: Parameters<typeof useDataSourceApi>) => mockUseDataSourceApi(...args),
}));

jest.mock("./DataSourceError", () => ({
  DataSourceError: () => <div data-testid="data-source-error" />,
}));
jest.mock("./properties/LoadingProperties", () => ({
  LoadingDataSourceProperties: () => <div data-testid="loading-properties" />,
}));
jest.mock("./properties/AWSProperties", () => ({
  AWSDataSourceProperties: ({ entity }: MockPropertiesProps) => (
    <div data-testid="aws-properties">{entity.id}</div>
  ),
}));
jest.mock("./properties/AzureProperties", () => ({
  AzureDataSourceProperties: ({ entity }: MockPropertiesProps) => (
    <div data-testid="azure-properties">{entity.id}</div>
  ),
}));
jest.mock("./properties/GCPProperties", () => ({
  GCPDataSourceProperties: ({ entity }: MockPropertiesProps) => (
    <div data-testid="gcp-properties">{entity.id}</div>
  ),
}));
jest.mock("./properties/UnknownProperties", () => ({
  UnknownDataSourceProperties: ({ entity }: MockPropertiesProps) => (
    <div data-testid="unknown-properties">{entity.id}</div>
  ),
}));

function prime(result: Partial<UseDataSourceApiResult>) {
  mockUseDataSourceApi.mockReturnValue(result as UseDataSourceApiResult);
}

function renderDetails() {
  return renderWithOrganizationRoute(<DataSourceDetails />, {
    initialUrl: "/organizations/org-1/data-sources/ds-1/details",
    routePath: "/organizations/:organizationId/data-sources/:dataSourceId/details",
  });
}

describe("DataSourceDetails", () => {
  it("queries the data source using the route params", () => {
    prime({ isLoading: true });

    renderDetails();

    expect(mockUseDataSourceApi).toHaveBeenCalledWith("org-1", "ds-1");
  });

  it("renders the loading properties while the data source is loading", () => {
    prime({ isLoading: true });

    renderDetails();

    expect(screen.getByTestId("loading-properties")).toBeInTheDocument();
  });

  it("renders the error when the data source could not be loaded", () => {
    prime({ isLoading: false, data: undefined });

    renderDetails();

    expect(screen.getByTestId("data-source-error")).toBeInTheDocument();
  });

  it.each<[DatasourceDetailRead["type"], string]>([
    ["aws_cnr", "aws-properties"],
    ["azure_tenant", "azure-properties"],
    ["azure_cnr", "azure-properties"],
    ["gcp_cnr", "gcp-properties"],
    ["gcp_tenant", "gcp-properties"],
    ["unknown", "unknown-properties"],
  ])("renders the matching properties for a '%s' data source", (type, testId) => {
    prime({ isLoading: false, data: makeDatasourceDetail({ id: "ds-1", type }) });

    renderDetails();

    expect(screen.getByTestId(testId)).toHaveTextContent("ds-1");
  });
});
