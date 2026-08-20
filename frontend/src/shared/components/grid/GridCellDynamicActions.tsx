import { GridCellActions } from "@swo/design-system/grid";
import { ListOption } from "@swo/dropdown";

export interface GridCellDynamicActionsProps<TItem extends object, TAction extends string> {
  item: TItem;
  actions: ListOption<TAction>[];
}

export function GridCellDynamicActions<
  TItem extends object = object,
  TAction extends string = string,
>({ item, actions }: GridCellDynamicActionsProps<TItem, TAction>) {
  return actions.length > 0 ? <GridCellActions actions={actions} item={item} /> : <></>;
}
