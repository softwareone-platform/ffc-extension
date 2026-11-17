import { render, screen } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import { highlightValues, makeDatasourceDetail } from "~test-utils";
import { mockDesignSystemUtilsGlobals } from "~test-utils/mocks/designSystemUtils";

import "./AzureProperties.spec.mocks";

import { AzureDataSourceProperties } from "./AzureProperties";

const { NO_VALUE } = mockDesignSystemUtilsGlobals;

function renderProperties(overrides: Partial<DatasourceDetailRead>) {
  return render(
    <AzureDataSourceProperties
      entity={makeDatasourceDetail({ type: "azure_cnr", ...overrides })}
    />,
  );
}

describe("AzureDataSourceProperties", () => {
  it("renders the formatted connection date and additional ids", () => {
    renderProperties({
      details: {
        connected_at: "2026-01-15T10:00:00Z",
        subscription_id: "sub-1",
        tenant_id: "tenant-1",
        client_id: "client-1",
      },
    });

    expect(highlightValues()).toMatchObject({
      connected_at: "date(2026-01-15T10:00:00Z)",
      subscription_id: "sub-1",
      tenant_id: "tenant-1",
      client_id: "client-1",
    });
  });

  it("leaves the connection date empty when the data source was never connected", () => {
    renderProperties({ details: { connected_at: null } });

    expect(highlightValues().connected_at).toBe("");
  });

  it("links the parent data source to its sibling details page", () => {
    renderProperties({
      parent: { id: "p-1", name: "Tenant", type: "azure_tenant", datasource_id: "tenant-123" },
    });

    expect(screen.getByRole("link", { name: "Tenant" })).toHaveAttribute(
      "href",
      "../../p-1/details",
    );
    expect(screen.getByTestId("secondary")).toHaveTextContent("tenant-123");
    expect(screen.getByTestId("custom-icon")).toHaveTextContent("azure_tenant");
  });

  it("falls back to NO_VALUE as parent secondary content when it has no datasource_id", () => {
    renderProperties({ parent: { id: "p-1", name: "Tenant", type: "azure_tenant" } });

    expect(screen.getByTestId("secondary")).toHaveTextContent(NO_VALUE);
  });

  it("shows NO_VALUE for the parent when the data source has none", () => {
    renderProperties({ parent: null });

    expect(screen.queryByTestId("entity-reference-cell")).not.toBeInTheDocument();
    expect(highlightValues().parent).toBe(NO_VALUE);
  });
});
