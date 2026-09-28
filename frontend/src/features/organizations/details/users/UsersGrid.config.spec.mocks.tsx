import type { ComponentProps } from "react";

import type { useOrganizationsApi } from "~organizations/api";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockGridCellDate, mockGridCellDynamicActions } from "~test-utils/mocks/sharedGridCells";
import {
  mockGridInfoDialogConfigurationModule,
  mockReactQueryRqlGridModule,
} from "~test-utils/mocks/sharedGridHooks";
import { mockUserRoleModule } from "~test-utils/mocks/userRole";

import type { useActionOptions } from "./hooks/useActionOptions";

export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";
export {
  mockUseGridInfoDialogConfiguration,
  mockUseReactQueryRqlGrid,
} from "~test-utils/mocks/sharedGridHooks";
export { mockUseUserRole } from "~test-utils/mocks/userRole";

type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;
type MockGridCellTitleSubtitleProps = ComponentProps<
  typeof import("@swo/design-system/grid").GridCellTitleSubtitle
>;
type MockStatusChipProps = ComponentProps<typeof import("@swo/mp-status-chip").StatusChip>;

export const mockGetActions = jest.fn() as jest.MockedFunction<ReturnType<typeof useActionOptions>>;
export const mockListOrganizationEmployees = jest.fn() as jest.MockedFunction<
  OrganizationsApi["listOrganizationEmployees"]
>;

jest.mock("@swo/design-system/grid", () => ({
  ...mockDesignSystemGrid,
  GridCellTitleSubtitle: ({ title, subtitle }: MockGridCellTitleSubtitleProps) => (
    <div>
      <span data-testid="title">{title}</span>
      <span data-testid="subtitle">{subtitle}</span>
    </div>
  ),
}));

jest.mock("@swo/mp-status-chip", () => ({
  StatusChip: ({ status, color }: MockStatusChipProps) => (
    <span data-testid="status-chip" data-color={color}>
      {status}
    </span>
  ),
}));

jest.mock("~shared/components/grid/GridCellDate", () => mockGridCellDate);
jest.mock("~shared/components/grid/GridCellDynamicActions", () => mockGridCellDynamicActions);
jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);
jest.mock(
  "~shared/hooks/useGridInfoDialogConfiguration",
  () => mockGridInfoDialogConfigurationModule,
);
jest.mock("~shared/hooks/useReactQueryRqlGrid", () => mockReactQueryRqlGridModule);

jest.mock("~organizations/api", () => ({
  useOrganizationsApi: () => ({
    listOrganizationEmployees: mockListOrganizationEmployees,
  }),
}));

jest.mock("./hooks/useActionOptions", () => ({
  useActionOptions: () => mockGetActions,
}));
