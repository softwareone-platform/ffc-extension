import { useCallback, useMemo } from "react";

import { AxiosRequestConfig } from "axios";

import { EntitlementCreate, EntitlementRead } from "@swo/ffc-api-model";
import { RqlQuery } from "@swo/rql-client";

import { http } from "@mpt-extension/sdk";

import { ListResponse } from "~shared/utils/mapAxiosResponseDataList";

const rootPath = "/ops/v1/entitlements";

export function useEntitlementsApi() {
  const list = useCallback(
    async (
      query: RqlQuery<EntitlementRead>,
      config?: AxiosRequestConfig<ListResponse<EntitlementRead>>,
    ) => {
      return http<ListResponse<EntitlementRead>>({
        method: "GET",
        url: `${rootPath}${query ? `?${query.toString()}` : ""}`,
        ...config,
      });
    },
    [],
  );

  const get = useCallback(async (entityId: string, query?: RqlQuery<EntitlementRead>) => {
    return http<EntitlementRead>({
      method: "GET",
      url: `${rootPath}/${entityId}${query ? `?${query.toString()}` : ""}`,
    });
  }, []);

  const save = useCallback(async (entity: EntitlementCreate) => {
    return http<EntitlementCreate & { id?: string }>(
      "id" in entity && entity.id
        ? {
            method: "PUT",
            url: `${rootPath}/${entity.id}`,
            data: entity,
          }
        : {
            method: "POST",
            url: rootPath,
            data: entity,
          },
    );
  }, []);

  return useMemo(() => ({ list, get, save }), [list, get, save]);
}
