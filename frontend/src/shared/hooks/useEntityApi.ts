import { useCallback, useMemo } from "react";

import { AxiosRequestConfig } from "axios";

import { RqlQuery } from "@swo/rql-client";

import { http } from "@mpt-extension/sdk";

import { ListResponse } from "~shared/utils/mapAxiosResponseDataList";
import { getCustomQueryString } from "~shared/utils/rqlHelper";

/**
 * @typeParam Entity Read model returned by `list` / `get` / `remove`
 * @typeParam EntityCreate Body accepted by `save` (e.g. a `*Create` model); defaults to `Entity`
 * @typeParam EntityCreated Body returned by `save`; defaults to `Entity`
 */
export function useEntityApi<
  Entity extends object,
  EntityCreate extends object = Entity,
  EntityCreated = Entity,
>(rootPath: string) {
  const list = useCallback(
    (query: RqlQuery<Entity>, config?: AxiosRequestConfig<ListResponse<Entity>>) => {
      return http<ListResponse<Entity>>({
        method: "GET",
        url: rootPath + getCustomQueryString<Entity>(query),
        ...config,
      });
    },
    [rootPath],
  );

  const get = useCallback(
    (entityId: string, query?: RqlQuery<Entity>) => {
      return http<Entity>({
        method: "GET",
        url: `${rootPath}/${entityId}` + getCustomQueryString<Entity>(query),
      });
    },
    [rootPath],
  );

  const save = useCallback(
    (entity: EntityCreate) => {
      const id = "id" in entity && typeof entity.id === "string" ? entity.id : "";
      return http<EntityCreated>({
        method: id ? "PUT" : "POST",
        url: id ? `${rootPath}/${id}` : rootPath,
        data: entity,
      });
    },
    [rootPath],
  );

  const remove = useCallback(
    (entityId: string) => {
      return http<Entity>({
        method: "DELETE",
        url: `${rootPath}/${entityId}`,
      });
    },
    [rootPath],
  );

  return useMemo(() => ({ list, get, save, remove }), [list, get, save, remove]);
}
