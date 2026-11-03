import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import type { PageShell } from "~shared/components/page-shell";

import type { useDataSourceApi } from "../api/useDataSourceApi";
import { DataSourceDetailsHeader } from "./DataSourceDetailsHeader";

type MockPageShellHeaderProps = ComponentProps<typeof PageShell.Header>;
type UseDataSourceApiResult = ReturnType<typeof useDataSourceApi>;

const mockUseDataSourceApi = jest.fn() as jest.MockedFunction<typeof useDataSourceApi>;
const mockPageShellHeader = jest.fn() as jest.MockedFunction<
  (props: MockPageShellHeaderProps) => void
>;

jest.mock("../api/useDataSourceApi", () => ({
  useDataSourceApi: (...args: Parameters<typeof useDataSourceApi>) => mockUseDataSourceApi(...args),
}));

jest.mock("~shared/components/page-shell", () => ({
  PageShell: {
    Header: (props: MockPageShellHeaderProps) => {
      mockPageShellHeader(props);
      return <div data-testid="page-shell-header">{"title" in props ? props.title : null}</div>;
    },
  },
}));

function primeEntity(entity: Partial<DatasourceDetailRead> | undefined) {
  mockUseDataSourceApi.mockReturnValue({ data: entity } as unknown as UseDataSourceApiResult);
}

function renderHeader() {
  return render(
    <DataSourceDetailsHeader organizationId="org-1" dataSourceId="ds-1" backUrl="/back" />,
  );
}

function lastHeaderProps() {
  return mockPageShellHeader.mock.lastCall![0];
}

describe("DataSourceDetailsHeader", () => {
  it("queries the data source for the supplied organization and data source ids", () => {
    primeEntity(undefined);

    renderHeader();

    expect(mockUseDataSourceApi).toHaveBeenCalledWith("org-1", "ds-1");
  });

  it("links back to the supplied backUrl", () => {
    primeEntity(undefined);

    renderHeader();

    expect(lastHeaderProps().backUrl).toBe("/back");
  });

  it("shows the external datasource_id as title and the name as subtitle when loaded", () => {
    primeEntity({ id: "ds-1", name: "AWS Prod", datasource_id: "aws-prod-123" });

    renderHeader();

    expect(screen.getByTestId("page-shell-header")).toHaveTextContent("aws-prod-123");
    expect(lastHeaderProps().subtitle).toBe("AWS Prod");
  });

  it("falls back to a generic subtitle when the data source has no name", () => {
    primeEntity(undefined);

    renderHeader();

    expect(lastHeaderProps().subtitle).toBe("Data source details");
  });
});
