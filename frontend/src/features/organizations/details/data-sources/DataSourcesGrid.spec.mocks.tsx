import type { ComponentProps } from "react";

import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import type { useGridConfig } from "./DataSourcesGrid.config";
import type { DataSourceForceImportModal } from "./force-import-modal/DataSourceForceImportModal";

type MockDataSourceForceImportModalProps = ComponentProps<typeof DataSourceForceImportModal>;

export const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;
export const mockForceImportModal = jest.fn() as jest.MockedFunction<
  (props: MockDataSourceForceImportModalProps) => void
>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);

jest.mock("./DataSourcesGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof import("./DataSourcesGrid.config").useGridConfig>) =>
    mockUseGridConfig(...args),
}));

jest.mock("./force-import-modal/DataSourceForceImportModal", () => ({
  DataSourceForceImportModal: (props: MockDataSourceForceImportModalProps) => {
    mockForceImportModal(props);
    return <div data-testid="force-import-modal" />;
  },
}));
