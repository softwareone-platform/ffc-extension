import type { GridCellDateProps } from "~shared/components/grid/GridCellDate";

export const mockGridCellDate = {
  GridCellDate: ({ value }: GridCellDateProps) => (
    <div data-testid="grid-cell-date">{String(value)}</div>
  ),
};
