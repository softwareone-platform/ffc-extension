import { render } from "@testing-library/react";

import { highlightValues, makeDatasourceDetail } from "~test-utils";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockEntityStatusChip, mockStatus } from "~test-utils/mocks/entityStatusChip";
import { mockFormatDate, mockFormatDateModule } from "~test-utils/mocks/formatDate";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { MonitoringMetrics } from "./MonitoringMetrics";

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("~shared/components/entity-status-chip", () => mockEntityStatusChip);
jest.mock("~shared/hooks/useFormatDate", () => mockFormatDateModule);

describe("MonitoringMetrics", () => {
  it("renders the formatted metrics retrieval dates and status", () => {
    const entity = makeDatasourceDetail({
      metrics: {
        last_retrieval_at: "2026-01-15T10:00:00Z",
        last_attempt_at: "2026-01-16T10:00:00Z",
        status: "completed",
      },
    });

    render(<MonitoringMetrics entity={entity} />);

    expect(highlightValues()).toEqual({
      metrics_last_retrieval: "date(2026-01-15T10:00:00Z)",
      metrics_last_attempt: "date(2026-01-16T10:00:00Z)",
      status: "completed",
    });
  });

  it("passes empty values to the formatters when metrics info is missing", () => {
    const entity = makeDatasourceDetail({ metrics: undefined });

    render(<MonitoringMetrics entity={entity} />);

    expect(mockFormatDate.mock.calls).toEqual([[""], [""]]);
    expect(mockStatus).toHaveBeenCalledWith({ status: "" });
  });
});
