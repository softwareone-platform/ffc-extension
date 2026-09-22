import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import {
  mockCustomIcon,
  mockGridCellCurrency,
  mockGridCellDate,
  mockGridCellDynamicActions,
} from "~test-utils/mocks/sharedGridCells";

export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";

export const mockUseOrganizationContext = jest.fn();
export const mockListOrganizationDataSources = jest.fn();
export const mockUseReactQueryRqlGrid = jest.fn();
export const mockUseUserRole = jest.fn();
export const mockUseGridInfoDialogConfiguration = jest.fn();
export const mockGetActions = jest.fn();

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
