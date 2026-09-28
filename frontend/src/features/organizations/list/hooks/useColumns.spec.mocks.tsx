import type { ComponentProps } from "react";

import type { Link } from "react-router-dom";

import { Status } from "~shared/components/entity-status-chip/EntityStatusChip";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockGridCellDynamicActions } from "~test-utils/mocks/sharedGridCells";
import { mockUserRoleModule } from "~test-utils/mocks/userRole";

import type { useActionOptions } from "./useActionOptions";

export { mockUseUserRole } from "~test-utils/mocks/userRole";

type MockGridCellDateTimeProps = ComponentProps<
  typeof import("@swo/design-system/grid").GridCellDateTime
>;
type MockGridCellTitleSubtitleProps = ComponentProps<
  typeof import("@swo/design-system/grid").GridCellTitleSubtitle
>;
type MockStatusProps = ComponentProps<typeof Status>;

export const mockGetActions = jest.fn() as jest.MockedFunction<ReturnType<typeof useActionOptions>>;
export const mockStatus = jest.fn() as jest.MockedFunction<(props: MockStatusProps) => void>;

jest.mock("@swo/design-system/grid", () => ({
  ...mockDesignSystemGrid,
  GridCellDateTime: ({ date }: MockGridCellDateTimeProps) => (
    <span data-testid="grid-cell-date-time">{(date as string | undefined) ?? "no-date"}</span>
  ),
  GridCellTitleSubtitle: ({ title, subtitle }: MockGridCellTitleSubtitleProps) => (
    <div data-testid="grid-cell-title-subtitle">
      <span data-testid="title">{title}</span>
      <span data-testid="subtitle">{subtitle}</span>
    </div>
  ),
}));

jest.mock("~shared/components/entity-status-chip/EntityStatusChip", () => ({
  Status: (props: MockStatusProps) => {
    mockStatus(props);
    return <span data-testid="status" />;
  },
}));

jest.mock("~shared/components/grid/GridCellDynamicActions", () => mockGridCellDynamicActions);
jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, Link: ({ children }: ComponentProps<typeof Link>) => <>{children}</> };
});

jest.mock("./useActionOptions", () => ({
  useActionOptions: () => mockGetActions,
}));
