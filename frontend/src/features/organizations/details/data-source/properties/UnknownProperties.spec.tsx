import { render } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import { highlightValues, makeDatasourceDetail } from "~test-utils";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockFormatDateModule } from "~test-utils/mocks/formatDate";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { UnknownDataSourceProperties } from "./UnknownProperties";

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("~shared/hooks/useFormatDate", () => mockFormatDateModule);

function renderProperties(details: DatasourceDetailRead["details"]) {
  return render(
    <UnknownDataSourceProperties entity={makeDatasourceDetail({ type: "unknown", details })} />,
  );
}

describe("UnknownDataSourceProperties", () => {
  it("renders only the formatted connection date", () => {
    renderProperties({ connected_at: "2026-01-15T10:00:00Z" });

    expect(highlightValues()).toEqual({ connected_at: "date(2026-01-15T10:00:00Z)" });
  });

  it("leaves the connection date empty when the data source has no details", () => {
    renderProperties(undefined);

    expect(highlightValues()).toEqual({ connected_at: "" });
  });
});
