import { render } from "@testing-library/react";

import type { DatasourceDiscoveryItem } from "~api/ffc-api-model";
import { makeDatasourceDetail } from "~test-utils";
import { mockDesignSystemGrid, mockGridProps } from "~test-utils/mocks/designSystemGrid";

import { DiscoveryGrid } from "./DiscoveryGrid";
import type { useGridConfig } from "./DiscoveryGrid.config";

const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("./DiscoveryGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof useGridConfig>) => mockUseGridConfig(...args),
}));

describe("DiscoveryGrid", () => {
  beforeEach(() => {
    mockUseGridConfig.mockReturnValue({ id: "discovery-grid" } as unknown as ReturnType<
      typeof useGridConfig
    >);
  });

  it("configures the grid with the data source discovery items", () => {
    const discovery: DatasourceDiscoveryItem[] = [
      { resource_type: "instance", status: "completed" },
    ];

    render(<DiscoveryGrid dataSource={makeDatasourceDetail({ discovery })} />);

    expect(mockUseGridConfig).toHaveBeenCalledWith(discovery);
  });

  it("configures the grid with no items when the data source has no discovery", () => {
    render(<DiscoveryGrid dataSource={makeDatasourceDetail({ discovery: null })} />);

    expect(mockUseGridConfig).toHaveBeenCalledWith([]);
  });

  it("renders the grid with the configured props", () => {
    render(<DiscoveryGrid dataSource={makeDatasourceDetail()} />);

    expect(mockGridProps).toHaveBeenCalledWith(expect.objectContaining({ id: "discovery-grid" }));
  });
});
