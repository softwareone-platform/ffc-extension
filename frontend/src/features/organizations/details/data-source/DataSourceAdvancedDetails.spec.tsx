import type { ComponentProps } from "react";

import { screen } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import type { useDataSourceApi } from "~features/organizations/api/useDataSourceApi";
import { makeDatasourceDetail, renderWithOrganizationRoute } from "~test-utils";

import { DataSourceAdvancedDetails } from "./DataSourceAdvancedDetails";
import type { LoadingDataSourceProperties } from "./properties/LoadingProperties";

type UseDataSourceApiResult = ReturnType<typeof useDataSourceApi>;
type MockSectionProps = { entity: DatasourceDetailRead };
type MockLoadingProps = ComponentProps<typeof LoadingDataSourceProperties>;

const mockUseDataSourceApi = jest.fn() as jest.MockedFunction<typeof useDataSourceApi>;

jest.mock("~features/organizations/api/useDataSourceApi", () => ({
  useDataSourceApi: (...args: Parameters<typeof useDataSourceApi>) => mockUseDataSourceApi(...args),
}));

jest.mock("./DataSourceError", () => ({
  DataSourceError: () => <div data-testid="data-source-error" />,
}));
jest.mock("./properties/LoadingProperties", () => ({
  LoadingDataSourceProperties: ({ title }: MockLoadingProps) => (
    <div data-testid="loading-properties">{title}</div>
  ),
}));
jest.mock("./advanced/BillingImport", () => ({
  BillingImport: ({ entity }: MockSectionProps) => (
    <div data-testid="billing-import">{entity.id}</div>
  ),
}));
jest.mock("./advanced/MonitoringMetrics", () => ({
  MonitoringMetrics: ({ entity }: MockSectionProps) => (
    <div data-testid="monitoring-metrics">{entity.id}</div>
  ),
}));
jest.mock("./advanced/Discovery", () => ({
  Discovery: ({ entity }: MockSectionProps) => <div data-testid="discovery">{entity.id}</div>,
}));

function prime(result: Partial<UseDataSourceApiResult>) {
  mockUseDataSourceApi.mockReturnValue(result as UseDataSourceApiResult);
}

function renderAdvancedDetails() {
  return renderWithOrganizationRoute(<DataSourceAdvancedDetails />, {
    initialUrl: "/organizations/org-1/data-sources/ds-1/advanced",
    routePath: "/organizations/:organizationId/data-sources/:dataSourceId/advanced",
  });
}

describe("DataSourceAdvancedDetails", () => {
  it("queries the data source using the route params", () => {
    prime({ isLoading: true });

    renderAdvancedDetails();

    expect(mockUseDataSourceApi).toHaveBeenCalledWith("org-1", "ds-1");
  });

  it("renders a billing import loading section while the data source is loading", () => {
    prime({ isLoading: true });

    renderAdvancedDetails();

    expect(screen.getByTestId("loading-properties")).toHaveTextContent("billing_import");
    expect(screen.queryByTestId("billing-import")).not.toBeInTheDocument();
  });

  it("renders the error when the data source could not be loaded", () => {
    prime({ isLoading: false, data: undefined });

    renderAdvancedDetails();

    expect(screen.getByTestId("data-source-error")).toBeInTheDocument();
  });

  it.each(["billing-import", "monitoring-metrics", "discovery"])(
    "renders the %s section for the loaded data source",
    (testId) => {
      prime({ isLoading: false, data: makeDatasourceDetail({ id: "ds-1" }) });

      renderAdvancedDetails();

      expect(screen.getByTestId(testId)).toHaveTextContent("ds-1");
    },
  );
});
