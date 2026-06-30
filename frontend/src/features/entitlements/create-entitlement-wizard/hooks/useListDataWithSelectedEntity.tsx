import { useMemo } from "react";

interface UseListDataWithSelectedEntityProps<
  T extends {
    id?: string;
  },
> {
  entity?: T | null;
  data?: T[];
  isToShowEmptyValue?: boolean;
  unassignedEntity?: T | null;
}

export function useListDataWithSelectedEntity<T extends { id?: string }>({
  entity,
  data,
  isToShowEmptyValue,
  unassignedEntity,
}: UseListDataWithSelectedEntityProps<T>): T[] {
  const dataWithEmptyValue = useMemo<T[]>(
    () =>
      isToShowEmptyValue && unassignedEntity ? [unassignedEntity, ...(data || [])] : data || [],
    [data, isToShowEmptyValue, unassignedEntity],
  );
  return useMemo(
    () =>
      !entity?.id || dataWithEmptyValue?.some((x) => x && x.id === entity?.id)
        ? dataWithEmptyValue
        : [entity, ...dataWithEmptyValue],
    [dataWithEmptyValue, entity],
  );
}
