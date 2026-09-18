export const mockCustomIcon = {
  __esModule: true,
  default: ({ name }: { name: string }) => <div data-testid="custom-icon">{name}</div>,
};

export const mockGridCellCurrency = {
  GridCellCurrency: ({ value, currency }: { value: number; currency: string }) => (
    <div data-testid="grid-cell-currency">{`${value}|${currency}`}</div>
  ),
};

export const mockGridCellDate = {
  GridCellDate: ({ value }: { value: unknown }) => (
    <div data-testid="grid-cell-date">{String(value)}</div>
  ),
};

export const mockGridCellDynamicActions = {
  GridCellDynamicActions: ({ item, actions }: { item: unknown; actions: unknown }) => (
    <div data-testid="grid-cell-dynamic-actions">
      <span data-testid="actions-item-id">{(item as { id?: string }).id}</span>
      <span data-testid="actions-count">{Array.isArray(actions) ? actions.length : 0}</span>
    </div>
  ),
};
