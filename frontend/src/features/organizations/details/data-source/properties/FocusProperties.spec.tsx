import { render } from "@testing-library/react";

import type { DatasourceDetailRead } from "~api/ffc-api-model";
import { highlightValues, makeDatasourceDetail } from "~test-utils";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import {
  mockDesignSystemUtils,
  mockDesignSystemUtilsGlobals,
} from "~test-utils/mocks/designSystemUtils";
import { mockFormatDateModule } from "~test-utils/mocks/formatDate";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { FocusProperties } from "./FocusProperties";

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("~shared/hooks/useFormatDate", () => mockFormatDateModule);

const { NO_VALUE } = mockDesignSystemUtilsGlobals;

function renderProperties(details: DatasourceDetailRead["details"]) {
  return render(
    <FocusProperties entity={makeDatasourceDetail({ id: "ds-focus", type: "focus", details })} />,
  );
}

describe("FocusProperties", () => {
  it("renders the formatted connection date and the data source id", () => {
    renderProperties({ connected_at: "2026-01-15T10:00:00Z" } as DatasourceDetailRead["details"]);

    expect(highlightValues()).toEqual({
      connected_at: "date(2026-01-15T10:00:00Z)",
      id: "ds-focus",
    });
  });

  it("shows NO_VALUE for the connection date when the data source was never connected", () => {
    renderProperties({ connected_at: null } as DatasourceDetailRead["details"]);

    expect(highlightValues().connected_at).toBe(NO_VALUE);
  });
});
