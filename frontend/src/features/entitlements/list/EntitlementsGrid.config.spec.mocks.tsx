import type { ComponentProps } from "react";

import type { Link } from "react-router-dom";

import type { useEntitlementsApi } from "~entitlements/api";
import type { DataSourceEntityReference } from "~features/entitlements/components/DataSourceEntityReference";
import type { Status } from "~shared/components/entity-status-chip/EntityStatusChip";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockCustomIcon, mockGridCellDynamicActions } from "~test-utils/mocks/sharedGridCells";
import {
  mockGridIdentityModule,
  mockGridInfoDialogConfigurationModule,
  mockReactQueryRqlGridModule,
} from "~test-utils/mocks/sharedGridHooks";

import type { useActionOptions } from "./hooks/useActionOptions";

export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";
export {
  mockUseGridInfoDialogConfiguration,
  mockUseReactQueryRqlGrid,
} from "~test-utils/mocks/sharedGridHooks";

type EntitlementsApi = ReturnType<typeof useEntitlementsApi>;
type GridCellDateTimeProps = Pick<
  ComponentProps<typeof import("@swo/design-system/grid").GridCellDateTime>,
  "date"
>;
type GridCellTitleSubtitleProps = Pick<
  ComponentProps<typeof import("@swo/design-system/grid").GridCellTitleSubtitle>,
  "title" | "subtitle"
>;
type EntityReferenceProps = Pick<
  ComponentProps<typeof import("@swo/design-system/entity-reference").EntityReference>,
  "primaryContent" | "secondaryContent" | "icon"
>;
type StatusProps = ComponentProps<typeof Status<{ status: string }>>;
type DataSourceEntityReferenceProps = ComponentProps<typeof DataSourceEntityReference>;

export const mockListEntitlements = jest.fn() as jest.MockedFunction<EntitlementsApi["list"]>;
export const mockGetActions = jest.fn() as jest.MockedFunction<ReturnType<typeof useActionOptions>>;
export const mockStatus = jest.fn() as jest.MockedFunction<(props: StatusProps) => void>;

jest.mock("@swo/design-system/grid", () => ({
  ...mockDesignSystemGrid,
  GridCellDateTime: ({ date }: GridCellDateTimeProps) => (
    <span data-testid="grid-cell-date-time">{date ?? "no-date"}</span>
  ),
  GridCellTitleSubtitle: ({ title, subtitle }: GridCellTitleSubtitleProps) => (
    <div>
      <span data-testid="title">{title}</span>
      <span data-testid="subtitle">{subtitle}</span>
    </div>
  ),
}));

jest.mock("@swo/design-system/entity-reference", () => ({
  EntityReference: ({ primaryContent, secondaryContent, icon }: EntityReferenceProps) => (
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
  Status: (props: StatusProps) => {
    mockStatus(props);
    return <span data-testid="status" />;
  },
}));

jest.mock("../components/DataSourceEntityReference", () => ({
  DataSourceEntityReference: (props: DataSourceEntityReferenceProps) => (
    <div
      data-testid="datasource-entity-reference"
      data-entity-id={(props.entity as { id?: string }).id}
    />
  ),
}));

jest.mock("~entitlements/api", () => ({
  useEntitlementsApi: () => ({ list: mockListEntitlements }),
}));

jest.mock("~shared/hooks/useReactQueryRqlGrid", () => mockReactQueryRqlGridModule);

jest.mock(
  "~shared/hooks/useGridInfoDialogConfiguration",
  () => mockGridInfoDialogConfigurationModule,
);

jest.mock("~shared/hooks/useGridIdentity", () => mockGridIdentityModule);

jest.mock("./hooks/useActionOptions", () => ({
  useActionOptions: () => mockGetActions,
}));

jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, Link: ({ children }: ComponentProps<typeof Link>) => <>{children}</> };
});
