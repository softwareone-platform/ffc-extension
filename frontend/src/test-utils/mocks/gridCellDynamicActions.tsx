import type { GridCellDynamicActionsProps } from "~shared/components/grid/GridCellDynamicActions";

type MockGridCellDynamicActionsProps = GridCellDynamicActionsProps<{ id?: string }, string>;

export const mockGridCellDynamicActions = {
  GridCellDynamicActions: ({ item, actions }: MockGridCellDynamicActionsProps) => (
    <div data-testid="grid-cell-dynamic-actions">
      <span data-testid="actions-item-id">{item.id}</span>
      <span data-testid="actions-count">{Array.isArray(actions) ? actions.length : 0}</span>
    </div>
  ),
};
