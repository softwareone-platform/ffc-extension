import type { DatasourceDetailRead } from "~api/ffc-api-model";

export function getPropertyValue(
  entity: DatasourceDetailRead | null | undefined,
  property: string,
) {
  return entity?.details && property in entity.details
    ? (entity.details as Record<string, unknown>)[property]
    : undefined;
}
