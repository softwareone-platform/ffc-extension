import type { ComponentProps } from "react";

import type { GridCellSimple } from "@swo/design-system/grid";

type MockGridCellSimpleProps = Pick<ComponentProps<typeof GridCellSimple>, "children">;

export const mockGridProps = jest.fn();
export const mockUseGridAsync = jest.fn();

export const mockDesignSystemGrid = {
  Grid: (props: unknown) => {
    mockGridProps(props);
    return <div data-testid="grid" />;
  },
  GridCellSimple: ({ children }: MockGridCellSimpleProps) => (
    <div data-testid="grid-cell-simple">{children}</div>
  ),
  useGridAsync: (config: unknown) => mockUseGridAsync(config),
  buildRqlQuery: jest.fn(),
};
