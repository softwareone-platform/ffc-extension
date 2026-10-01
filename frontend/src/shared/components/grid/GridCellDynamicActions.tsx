import { ListOption } from "@swo/design-system/dropdown";
import { GridCellActions } from "@swo/design-system/grid";
import { NO_VALUE } from "@swo/design-system/utils";

export interface GridCellDynamicActionsProps<TItem extends object, TAction extends string> {
  item: TItem;
  actions: ListOption<TAction>[];
}

export function GridCellDynamicActions<
  TItem extends object = object,
  TAction extends string = string,
>({ item, actions }: GridCellDynamicActionsProps<TItem, TAction>) {
  return actions.length > 0 ? <GridCellActions actions={actions} item={item} /> : <>{NO_VALUE}</>;
}
