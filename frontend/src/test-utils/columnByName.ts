import type { GridColumnDefinition } from "@swo/design-system/grid";

type NamedGridColumn = Pick<GridColumnDefinition<object>, "name">;

export function columnByName<T extends NamedGridColumn>(cols: readonly T[], name: string): T {
  const column = cols.find((c) => c.name === name);
  if (!column) throw new Error(`column '${name}' not found`);
  return column;
}
