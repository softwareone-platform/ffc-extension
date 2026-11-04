import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityStatusChip } from "~test-utils/mocks/entityStatusChip";
import { mockGridCellDate } from "~test-utils/mocks/gridCellDate";
import {
  mockGridIdentityModule,
  mockGridInfoDialogConfigurationModule,
} from "~test-utils/mocks/gridHooks";

export { mockUseGridInMemory } from "~test-utils/mocks/designSystemGrid";
export { mockStatus } from "~test-utils/mocks/entityStatusChip";
export {
  mockUseGridIdentity,
  mockUseGridInfoDialogConfiguration,
} from "~test-utils/mocks/gridHooks";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("~shared/components/entity-status-chip/EntityStatusChip", () => mockEntityStatusChip);
jest.mock("~shared/components/grid/GridCellDate", () => mockGridCellDate);
jest.mock("~shared/hooks/useGridIdentity", () => mockGridIdentityModule);
jest.mock(
  "~shared/hooks/useGridInfoDialogConfiguration",
  () => mockGridInfoDialogConfigurationModule,
);
