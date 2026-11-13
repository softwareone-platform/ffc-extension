import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { makeDatasourceDetail } from "~test-utils/factories";

import {
  mockForceImportModal,
  mockPageShellHeader,
  mockUseDataSourceApi,
} from "./DataSourceDetailsHeader.spec.mocks";

import type { useDataSourceApi } from "../api/useDataSourceApi";
import { DataSourceDetailsHeader } from "./DataSourceDetailsHeader";

type UseDataSourceApiResult = ReturnType<typeof useDataSourceApi>;

const mockRefetch = jest.fn();

function primeEntity(entity: ReturnType<typeof makeDatasourceDetail> | undefined) {
  mockUseDataSourceApi.mockReturnValue({
    data: entity,
    refetch: mockRefetch,
  } as unknown as UseDataSourceApiResult);
}

function renderHeader() {
  return render(
    <DataSourceDetailsHeader organizationId="org-1" dataSourceId="ds-1" backUrl="/back" />,
  );
}

function lastHeaderProps() {
  return mockPageShellHeader.mock.lastCall![0];
}

async function openForceImport() {
  const user = userEvent.setup();
  renderHeader();
  await user.click(screen.getByRole("button", { name: "force_import" }));
  return user;
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
    primeEntity(makeDatasourceDetail({ name: "AWS Prod", datasource_id: "aws-prod-123" }));

    renderHeader();

    expect(screen.getByTestId("page-shell-header")).toHaveTextContent("aws-prod-123");
    expect(lastHeaderProps().subtitle).toBe("AWS Prod");
  });

  it("falls back to the breadcrumb subtitle when the data source is not loaded", () => {
    primeEntity(undefined);

    renderHeader();

    expect(lastHeaderProps().subtitle).toBe("breadcrumb");
  });

  it("renders a closed force-import modal scoped to the organization", () => {
    primeEntity(makeDatasourceDetail());

    renderHeader();

    expect(screen.getByTestId("force-import-modal")).toHaveAttribute("data-open", "false");
    expect(screen.getByTestId("force-import-modal")).toHaveAttribute(
      "data-organization-id",
      "org-1",
    );
  });

  it("opens the force-import modal with the loaded data source when the action is clicked", async () => {
    primeEntity(makeDatasourceDetail({ id: "ds-1" }));

    await openForceImport();

    expect(screen.getByTestId("force-import-modal")).toHaveAttribute("data-open", "true");
    expect(screen.getByTestId("force-import-modal")).toHaveAttribute("data-datasource-id", "ds-1");
  });

  it("refetches the data source after a successful force import", async () => {
    primeEntity(makeDatasourceDetail());
    const user = await openForceImport();

    await user.click(screen.getByRole("button", { name: "complete force import" }));

    expect(mockRefetch).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("force-import-modal")).toHaveAttribute("data-open", "false");
  });

  it("closes the force-import modal without refetching when it is cancelled", async () => {
    primeEntity(makeDatasourceDetail());
    const user = await openForceImport();

    await user.click(screen.getByRole("button", { name: "close force import modal" }));

    expect(mockRefetch).not.toHaveBeenCalled();
    expect(mockForceImportModal.mock.lastCall![0].datasource).toBeNull();
    expect(screen.getByTestId("force-import-modal")).toHaveAttribute("data-open", "false");
  });
});
