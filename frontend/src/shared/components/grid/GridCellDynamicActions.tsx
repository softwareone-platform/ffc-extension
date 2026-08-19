import { GridCellActions } from "@swo/design-system/grid";

export interface GridCellDynamicActionsProps<TItem extends object> {
  item: TItem;
  actions: any[];
}

export function GridCellDynamicActions<T extends object = object>({
  item,
  actions,
}: GridCellDynamicActionsProps<T>) {
  return actions.length > 0 ? <GridCellActions actions={actions} item={item} /> : <></>;
}
