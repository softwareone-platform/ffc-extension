import { render } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import { highlightValues, makeDatasourceDetail } from "~test-utils";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockFormatDateModule } from "~test-utils/mocks/formatDate";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { GCPDataSourceProperties } from "./GCPProperties";

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("~shared/hooks/useFormatDate", () => mockFormatDateModule);

function renderProperties(details: DatasourceDetailRead["details"]) {
  return render(
    <GCPDataSourceProperties entity={makeDatasourceDetail({ type: "gcp_cnr", details })} />,
  );
}

describe("GCPDataSourceProperties", () => {
  it("renders the formatted connection date, project and billing export details", () => {
    renderProperties({
      connected_at: "2026-01-15T10:00:00Z",
      project_id: "proj-1",
      billing_dataset_name: "billing_ds",
      billing_table_name: "billing_tbl",
      billing_project_id: "billing-proj",
    } as DatasourceDetailRead["details"]);

    expect(highlightValues()).toEqual({
      connected_at: "date(2026-01-15T10:00:00Z)",
      project_id: "proj-1",
      billing_dataset_name: "billing_ds",
      billing_table_name: "billing_tbl",
      billing_project_id: "billing-proj",
    });
  });

  it("leaves the connection date empty when the data source was never connected", () => {
    renderProperties({ connected_at: null });

    expect(highlightValues().connected_at).toBe("");
  });
});
