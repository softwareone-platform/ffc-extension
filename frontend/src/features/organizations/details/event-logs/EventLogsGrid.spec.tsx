import { render } from "@testing-library/react";

import { mockDesignSystemGrid, mockGridProps } from "~test-utils/mocks/designSystemGrid";

import { EventLogsGrid } from "./EventLogsGrid";
import type { useGridConfig } from "./EventLogsGrid.config";

const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("./EventLogsGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof useGridConfig>) => mockUseGridConfig(...args),
}));

describe("EventLogsGrid", () => {
  beforeEach(() => {
    mockUseGridConfig.mockReturnValue({ id: "event-logs-grid" } as unknown as ReturnType<
      typeof useGridConfig
    >);
  });

  it("configures the grid for the given organization", () => {
    render(<EventLogsGrid organizationId="org-123" />);

    expect(mockUseGridConfig).toHaveBeenCalledWith("org-123");
  });

  it("renders the grid with the configured props", () => {
    render(<EventLogsGrid organizationId="org-123" />);

    expect(mockGridProps).toHaveBeenCalledWith(expect.objectContaining({ id: "event-logs-grid" }));
  });
});
