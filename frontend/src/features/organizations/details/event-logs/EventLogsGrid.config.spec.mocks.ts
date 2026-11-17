import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import {
  mockGridIdentityModule,
  mockGridInfoDialogConfigurationModule,
} from "~test-utils/mocks/gridHooks";

import type { useAsyncOptions } from "./hooks/useAsyncOptions";
import type { useColumns } from "./hooks/useColumns";
import type { useFields } from "./hooks/useFields";
import type { useViews } from "./hooks/useViews";

export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";
export {
  mockUseGridIdentity,
  mockUseGridInfoDialogConfiguration,
} from "~test-utils/mocks/gridHooks";

export const mockUseColumns = jest.fn() as jest.MockedFunction<typeof useColumns>;
export const mockUseFields = jest.fn() as jest.MockedFunction<typeof useFields>;
export const mockUseViews = jest.fn() as jest.MockedFunction<typeof useViews>;
// useAsyncOptions wraps the generic useReactQueryRqlGrid — keep the spy loosely typed.
export const mockUseAsyncOptions = jest.fn() as jest.MockedFunction<
  (organizationId: Parameters<typeof useAsyncOptions>[0]) => unknown
>;

export type GridInfoDialogConfig = ReturnType<typeof useGridInfoDialogConfiguration>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("~shared/hooks/useGridIdentity", () => mockGridIdentityModule);
jest.mock(
  "~shared/hooks/useGridInfoDialogConfiguration",
  () => mockGridInfoDialogConfigurationModule,
);

jest.mock("./hooks/useColumns", () => ({ useColumns: () => mockUseColumns() }));
jest.mock("./hooks/useFields", () => ({ useFields: () => mockUseFields() }));
jest.mock("./hooks/useViews", () => ({ useViews: () => mockUseViews() }));
jest.mock("./hooks/useAsyncOptions", () => ({
  useAsyncOptions: (organizationId: string) => mockUseAsyncOptions(organizationId),
}));
