import type { ComponentProps } from "react";

import type {
  buildRqlQuery,
  Grid,
  GridCellDateTime,
  GridCellSimple,
  GridCellTitleSubtitle,
  UseAsyncGridConfig,
} from "@swo/design-system/grid";

type MockGridProps = ComponentProps<typeof Grid>;
type MockGridActionsProps = ComponentProps<typeof Grid.Actions>;
type MockGridCellSimpleProps = Pick<ComponentProps<typeof GridCellSimple>, "children">;
type MockGridCellDateTimeProps = ComponentProps<typeof GridCellDateTime>;
type MockGridCellTitleSubtitleProps = ComponentProps<typeof GridCellTitleSubtitle>;

export const mockGridProps = jest.fn() as jest.MockedFunction<(props: MockGridProps) => void>;
export const mockUseGridAsync = jest.fn() as jest.MockedFunction<
  (config: UseAsyncGridConfig<object>) => unknown
>;

export const mockDesignSystemGrid = {
  Grid: Object.assign(
    (props: MockGridProps) => {
      mockGridProps(props);
      return <div data-testid="grid">{props.children}</div>;
    },
    {
      Actions: ({ children }: MockGridActionsProps) => (
        <div data-testid="grid-actions">{children}</div>
      ),
    },
  ),
  GridCellSimple: ({ children }: MockGridCellSimpleProps) => (
    <div data-testid="grid-cell-simple">{children}</div>
  ),
  GridCellDateTime: ({ date }: MockGridCellDateTimeProps) => (
    <span data-testid="grid-cell-date-time">{(date as string | undefined) ?? "no-date"}</span>
  ),
  GridCellTitleSubtitle: ({ title, subtitle }: MockGridCellTitleSubtitleProps) => (
    <div data-testid="grid-cell-title-subtitle">
      <span data-testid="title">{title}</span>
      <span data-testid="subtitle">{subtitle}</span>
    </div>
  ),
  useGridAsync: (config: UseAsyncGridConfig<object>) => mockUseGridAsync(config),
  buildRqlQuery: jest.fn() as jest.MockedFunction<typeof buildRqlQuery>,
};
