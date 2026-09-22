import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

export const mockUseGridConfig = jest.fn();
export const mockForceImportModal = jest.fn();

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);

jest.mock("./DataSourcesGrid.config", () => ({
  useGridConfig: (
    ...args: Parameters<typeof import("./DataSourcesGrid.config").useGridConfig>
  ) => mockUseGridConfig(...args),
}));

jest.mock("./force-import-modal/DataSourceForceImportModal", () => ({
  DataSourceForceImportModal: (props: unknown) => {
    mockForceImportModal(props);
    return <div data-testid="force-import-modal" />;
  },
}));

