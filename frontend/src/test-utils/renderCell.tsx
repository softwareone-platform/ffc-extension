import { ReactNode } from "react";

import { render } from "@testing-library/react";

import { columnByName } from "./columnByName";

type CellColumn = { cell?: unknown; name?: string };

export function renderCell<T>(column: CellColumn, item: T) {
  const fn = column.cell as (item: T) => ReactNode;
  return render(<>{fn(item)}</>);
}

export function renderColumnCell<T>(
  cols: readonly CellColumn[],
  name: string,
  item: T,
) {
  return renderCell(columnByName(cols, name), item);
}
