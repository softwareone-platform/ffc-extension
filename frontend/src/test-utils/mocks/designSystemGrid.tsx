import { ReactNode } from "react";

export const mockGridProps = jest.fn();
export const mockUseGridAsync = jest.fn();

export const mockDesignSystemGrid = {
  Grid: (props: unknown) => {
    mockGridProps(props);
    return <div data-testid="grid" />;
  },
  GridCellSimple: ({ children }: { children: ReactNode }) => (
    <div data-testid="grid-cell-simple">{children}</div>
  ),
  useGridAsync: (config: unknown) => mockUseGridAsync(config),
  buildRqlQuery: jest.fn(),
};
