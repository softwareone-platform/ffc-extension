import type { ComponentProps } from "react";

import type CustomIcon from "~shared/components/custom-icons/CustomIcon";
import type { GridCellCurrencyProps } from "~shared/components/grid/GridCellCurrency";
import type { GridCellDateProps } from "~shared/components/grid/GridCellDate";
import type { GridCellDynamicActionsProps } from "~shared/components/grid/GridCellDynamicActions";

type MockCustomIconProps = Pick<ComponentProps<typeof CustomIcon>, "name">;
type MockGridCellCurrencyProps = Pick<GridCellCurrencyProps, "value" | "currency">;
type MockGridCellDynamicActionsProps = GridCellDynamicActionsProps<{ id?: string }, string>;

export const mockCustomIcon = {
  __esModule: true,
  default: ({ name }: MockCustomIconProps) => <div data-testid="custom-icon">{name}</div>,
};

export const mockGridCellCurrency = {
  GridCellCurrency: ({ value, currency }: MockGridCellCurrencyProps) => (
    <div data-testid="grid-cell-currency">{`${value}|${currency}`}</div>
  ),
};

export const mockGridCellDate = {
  GridCellDate: ({ value }: GridCellDateProps) => (
    <div data-testid="grid-cell-date">{String(value)}</div>
  ),
};

export const mockGridCellDynamicActions = {
  GridCellDynamicActions: ({ item, actions }: MockGridCellDynamicActionsProps) => (
    <div data-testid="grid-cell-dynamic-actions">
      <span data-testid="actions-item-id">{item.id}</span>
      <span data-testid="actions-count">{Array.isArray(actions) ? actions.length : 0}</span>
    </div>
  ),
};
