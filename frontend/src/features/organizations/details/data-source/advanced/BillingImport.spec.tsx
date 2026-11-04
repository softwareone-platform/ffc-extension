import { render } from "@testing-library/react";

import type { useDateDistance } from "~shared/hooks/useDateDistance";
import { highlightValues, makeDatasourceDetail } from "~test-utils";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockEntityStatusChip, mockStatus } from "~test-utils/mocks/entityStatusChip";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { BillingImport } from "./BillingImport";

type DateDistance = ReturnType<typeof useDateDistance>;

const mockDateDistance = jest.fn<ReturnType<DateDistance>, Parameters<DateDistance>>(
  (value) => `distance(${String(value)})`,
);

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("~shared/components/entity-status-chip", () => mockEntityStatusChip);
jest.mock("~shared/hooks/useDateDistance", () => ({
  useDateDistance: () => mockDateDistance,
}));

describe("BillingImport", () => {
  it("renders the relative billing import dates and status", () => {
    const entity = makeDatasourceDetail({
      billing: {
        last_report_processed_at: "2026-01-15T10:00:00Z",
        last_attempt_at: "2026-01-16T10:00:00Z",
        status: "failed",
      },
    });

    render(<BillingImport entity={entity} />);

    expect(highlightValues()).toEqual({
      last_report_processed_at: "distance(2026-01-15T10:00:00Z)",
      billing_last_attempt: "distance(2026-01-16T10:00:00Z)",
      status: "failed",
    });
    expect(mockStatus).toHaveBeenCalledWith({ status: "failed" });
  });

  it("passes empty values to the formatters when billing info is missing", () => {
    const entity = makeDatasourceDetail({ billing: undefined });

    render(<BillingImport entity={entity} />);

    expect(mockDateDistance.mock.calls).toEqual([[""], [""]]);
    expect(mockStatus).toHaveBeenCalledWith({ status: "" });
  });
});
