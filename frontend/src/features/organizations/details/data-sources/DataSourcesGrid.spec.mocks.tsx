import { mockDataSourceForceImportModalModule } from "~test-utils/mocks/dataSourceForceImportModal";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import type { useGridConfig } from "./DataSourcesGrid.config";

export { mockForceImportModal } from "~test-utils/mocks/dataSourceForceImportModal";

export const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);

jest.mock("./DataSourcesGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof import("./DataSourcesGrid.config").useGridConfig>) =>
    mockUseGridConfig(...args),
}));

jest.mock(
  "./force-import-modal/DataSourceForceImportModal",
  () => mockDataSourceForceImportModalModule,
);
