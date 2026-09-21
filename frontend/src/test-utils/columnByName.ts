export function columnByName<T extends { name?: string }>(
  cols: readonly T[],
  name: string,
): T {
  const column = cols.find((c) => c.name === name);
  if (!column) throw new Error(`column '${name}' not found`);
  return column;
}
