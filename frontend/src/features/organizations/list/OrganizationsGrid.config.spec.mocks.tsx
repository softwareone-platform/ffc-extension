import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import {
  mockGridIdentityModule,
  mockGridInfoDialogConfigurationModule,
} from "~test-utils/mocks/sharedGridHooks";
import { mockUserRoleModule } from "~test-utils/mocks/userRole";

export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";
export { mockUseGridInfoDialogConfiguration } from "~test-utils/mocks/sharedGridHooks";
export { mockUseUserRole } from "~test-utils/mocks/userRole";

export const mockUseColumns = jest.fn();
export const mockUseFields = jest.fn();
export const mockUseViews = jest.fn();
export const mockUseAsyncOptions = jest.fn();

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);

jest.mock("./hooks/useColumns", () => ({
  useColumns: () => mockUseColumns(),
}));

jest.mock("./hooks/useFields", () => ({
  useFields: () => mockUseFields(),
}));

jest.mock("./hooks/useViews", () => ({
  useViews: () => mockUseViews(),
}));

jest.mock("./hooks/useAsyncOptions", () => ({
  useAsyncOptions: () => mockUseAsyncOptions(),
}));

jest.mock(
  "~shared/hooks/useGridInfoDialogConfiguration",
  () => mockGridInfoDialogConfigurationModule,
);

jest.mock("~shared/hooks/useGridIdentity", () => mockGridIdentityModule);

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

