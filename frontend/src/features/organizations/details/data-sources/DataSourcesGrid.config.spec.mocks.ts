import type { useOrganizationsApi } from "~organizations/api";
import type { useOrganizationContext } from "~organizations/providers/OrganizationsProvider";
import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import type { useUserRole } from "~shared/hooks/useUserRole";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import {
  mockCustomIcon,
  mockGridCellCurrency,
  mockGridCellDate,
  mockGridCellDynamicActions,
} from "~test-utils/mocks/sharedGridCells";

import type { useActionOptions } from "./hooks/useActionOptions";

export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";

type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;

export const mockUseOrganizationContext = jest.fn() as jest.MockedFunction<
  typeof useOrganizationContext
>;
export const mockListOrganizationDataSources = jest.fn() as jest.MockedFunction<
  OrganizationsApi["listOrganizationDataSources"]
>;
export const mockUseReactQueryRqlGrid = jest.fn();
export const mockUseUserRole = jest.fn() as jest.MockedFunction<typeof useUserRole>;
export const mockUseGridInfoDialogConfiguration = jest.fn() as jest.MockedFunction<
  typeof useGridInfoDialogConfiguration
>;
export const mockGetActions = jest.fn() as jest.MockedFunction<ReturnType<typeof useActionOptions>>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);
jest.mock("~shared/components/grid/GridCellCurrency", () => mockGridCellCurrency);
jest.mock("~shared/components/grid/GridCellDate", () => mockGridCellDate);
jest.mock("~shared/components/grid/GridCellDynamicActions", () => mockGridCellDynamicActions);

jest.mock("~organizations/providers/OrganizationsProvider", () => ({
  useOrganizationContext: () => mockUseOrganizationContext(),
}));

jest.mock("~organizations/api", () => ({
  useOrganizationsApi: () => ({
    listOrganizationDataSources: mockListOrganizationDataSources,
  }),
}));

jest.mock("~shared/hooks/useReactQueryRqlGrid", () => ({
  useReactQueryRqlGrid: (...args: unknown[]) => mockUseReactQueryRqlGrid(...args),
}));

jest.mock("~shared/hooks/useUserRole", () => ({
  useUserRole: () => mockUseUserRole(),
}));

jest.mock("~shared/hooks/useGridInfoDialogConfiguration", () => ({
  useGridInfoDialogConfiguration: () => mockUseGridInfoDialogConfiguration(),
}));

jest.mock("./hooks/useActionOptions", () => ({
  useActionOptions: () => mockGetActions,
}));
