import { ReactNode } from "react";
import { render } from "@testing-library/react";
import type { GridColumnDefinition } from "@swo/design-system/grid";
import { columnByName } from "./columnByName";
type CellColumn<T extends object> = Pick<GridColumnDefinition<T>, "cell" | "name">;
export function renderCell<T extends object>(column: CellColumn<T>, item: T) {
  const fn = column.cell as (item: T) => ReactNode;
  return render(<>{fn(item)}</>);
}
export function renderColumnCell<T extends object>(
  cols: readonly CellColumn<T>[],
  name: string,
  item: T,
) {
  return renderCell(columnByName(cols, name), item);
}
