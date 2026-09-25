import type { ReactNode } from "react";

import type { useEntitlementsApi } from "~entitlements/api";
import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockCustomIcon, mockGridCellDynamicActions } from "~test-utils/mocks/sharedGridCells";

import type { useActionOptions } from "./hooks/useActionOptions";

export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";

type EntitlementsApi = ReturnType<typeof useEntitlementsApi>;

export const mockListEntitlements = jest.fn() as jest.MockedFunction<EntitlementsApi["list"]>;
export const mockUseReactQueryRqlGrid = jest.fn();
export const mockUseGridInfoDialogConfiguration = jest.fn() as jest.MockedFunction<
  typeof useGridInfoDialogConfiguration
>;
export const mockGetActions = jest.fn() as jest.MockedFunction<ReturnType<typeof useActionOptions>>;
export const mockStatus = jest.fn() as jest.MockedFunction<(props: { item: unknown }) => void>;

jest.mock("@swo/design-system/grid", () => ({
  ...mockDesignSystemGrid,
  GridCellDateTime: ({ date }: { date?: string }) => (
    <span data-testid="grid-cell-date-time">{date ?? "no-date"}</span>
  ),
  GridCellTitleSubtitle: ({ title, subtitle }: { title: ReactNode; subtitle: ReactNode }) => (
    <div>
      <span data-testid="title">{title}</span>
      <span data-testid="subtitle">{subtitle}</span>
    </div>
  ),
}));

jest.mock("@swo/design-system/entity-reference", () => ({
  EntityReference: ({
    primaryContent,
    secondaryContent,
    icon,
  }: {
    primaryContent: ReactNode;
    secondaryContent: ReactNode;
    icon?: ReactNode;
  }) => (
    <div data-testid="entity-reference">
      <span data-testid="entity-primary">{primaryContent}</span>
      <span data-testid="entity-secondary">{secondaryContent}</span>
      <span data-testid="entity-icon">{icon}</span>
    </div>
  ),
}));

jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);
jest.mock("~shared/components/grid/GridCellDynamicActions", () => mockGridCellDynamicActions);

jest.mock("~shared/components/entity-status-chip/EntityStatusChip", () => ({
  Status: (props: { item: unknown }) => {
    mockStatus(props);
    return <span data-testid="status" />;
  },
}));

jest.mock("../components/DataSourceEntityReference", () => ({
  DataSourceEntityReference: (props: { entity: unknown }) => (
    <div
      data-testid="datasource-entity-reference"
      data-entity-id={(props.entity as { id?: string }).id}
    />
  ),
}));

jest.mock("~entitlements/api", () => ({
  useEntitlementsApi: () => ({ list: mockListEntitlements }),
}));

jest.mock("~shared/hooks/useReactQueryRqlGrid", () => ({
  useReactQueryRqlGrid: (...args: unknown[]) => mockUseReactQueryRqlGrid(...args),
}));

jest.mock("~shared/hooks/useGridInfoDialogConfiguration", () => ({
  useGridInfoDialogConfiguration: () => mockUseGridInfoDialogConfiguration(),
}));

jest.mock("~shared/hooks/useGridIdentity", () => ({
  useGridIdentity: (id: string) => ({ id, memoizeId: id, storageParameters: ["unknown"] }),
}));

jest.mock("./hooks/useActionOptions", () => ({
  useActionOptions: () => mockGetActions,
}));

jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, Link: ({ children }: { children?: ReactNode }) => <>{children}</> };
});
