import type { GridCellCurrencyProps } from "~shared/components/grid/GridCellCurrency";

type MockGridCellCurrencyProps = Pick<GridCellCurrencyProps, "value" | "currency">;

export const mockGridCellCurrency = {
  GridCellCurrency: ({ value, currency }: MockGridCellCurrencyProps) => (
    <div data-testid="grid-cell-currency">{`${value}|${currency}`}</div>
  ),
};
