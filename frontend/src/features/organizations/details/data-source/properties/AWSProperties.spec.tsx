import { render, screen } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import { highlightValues, makeDatasourceDetail } from "~test-utils";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockFormatDateModule } from "~test-utils/mocks/formatDate";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { AWSDataSourceProperties } from "./AWSProperties";

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("~shared/hooks/useFormatDate", () => mockFormatDateModule);

function renderProperties(details: Record<string, unknown>) {
  const entity = makeDatasourceDetail({ details: details as DatasourceDetailRead["details"] });
  return render(<AWSDataSourceProperties entity={entity} />);
}

describe("AWSDataSourceProperties", () => {
  it("renders the formatted connection date and account details", () => {
    renderProperties({
      connected_at: "2026-01-15T10:00:00Z",
      account_id: "123456789012",
      account_type: "linked",
    });

    expect(highlightValues()).toMatchObject({
      connected_at: "date(2026-01-15T10:00:00Z)",
      account_id: "123456789012",
      account_type: "linked",
    });
  });

  it("leaves the connection date empty when the data source was never connected", () => {
    renderProperties({ connected_at: null });

    expect(highlightValues().connected_at).toBe("");
  });

  it("shows the assumed role name for assumed-role authentication", () => {
    renderProperties({ authentication_type: "assumed_role", assumed_role_name: "FinOpsRole" });

    expect(highlightValues()).toMatchObject({
      authentication_type: "assumed_role",
      assumed_role_name: "FinOpsRole",
    });
    expect(highlightValues()).not.toHaveProperty("access_key");
  });

  it("shows the access key id for access-key authentication", () => {
    renderProperties({ authentication_type: "access_key", access_key_id: "AKIA123" });

    expect(highlightValues()).toMatchObject({ access_key: "AKIA123" });
    expect(highlightValues()).not.toHaveProperty("assumed_role_name");
  });

  it("renders the export section for a standalone management account", () => {
    renderProperties({
      account_type: "management_standalone",
      export_type: "cur",
      export_name: "finops-export",
      bucket_name: "finops-bucket",
      bucket_prefix: "reports/",
      region_name: "eu-west-1",
    });

    expect(screen.getByText("export")).toBeInTheDocument();
    expect(highlightValues()).toMatchObject({
      export_type: "cur",
      export_name: "finops-export",
      bucket_name: "finops-bucket",
      bucket_prefix: "reports/",
      region_name: "eu-west-1",
    });
  });

  it("omits the export section for other account types", () => {
    renderProperties({ account_type: "linked", export_name: "finops-export" });

    expect(screen.queryByText("export")).not.toBeInTheDocument();
    expect(highlightValues()).not.toHaveProperty("export_name");
  });
});
