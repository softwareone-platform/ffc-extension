import type { ComponentProps } from "react";
import type { Grid, GridCellSimple, UseAsyncGridConfig } from "@swo/design-system/grid";
type MockGridProps = ComponentProps<typeof Grid>;
type MockGridCellSimpleProps = Pick<ComponentProps<typeof GridCellSimple>, "children">;
export const mockGridProps = jest.fn();
export const mockUseGridAsync = jest.fn();
export const mockDesignSystemGrid = {
  Grid: (props: MockGridProps) => {
    mockGridProps(props);
    return <div data-testid="grid" />;
  },
  GridCellSimple: ({ children }: MockGridCellSimpleProps) => {
    return <div data-testid="grid-cell-simple">{children}</div>;
  },
  useGridAsync: (config: UseAsyncGridConfig<object>) => mockUseGridAsync(config),
  buildRqlQuery: jest.fn(),
};
