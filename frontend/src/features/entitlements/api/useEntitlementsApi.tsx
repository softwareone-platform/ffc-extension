import { useCallback, useMemo } from "react";

import { AxiosRequestConfig } from "axios";

import { RqlQuery } from "@swo/rql-client";

import { http } from "@mpt-extension/sdk";

import { EntitlementCreate } from "~api/ffc-api-model";
import { ListResponse } from "~shared/utils/mapAxiosResponseDataList";
import { getCustomQueryString } from "~shared/utils/rqlHelper";

import { Entitlement } from "./model";

const rootPath = "/ops/v1/entitlements";

export function useEntitlementsApi() {
  const list = useCallback(
    async (
      query: RqlQuery<Entitlement>,
      config?: AxiosRequestConfig<ListResponse<Entitlement>>,
    ) => {
      return http<ListResponse<Entitlement>>({
        method: "GET",
        url: `${rootPath}${query ? `?${getCustomQueryString<Entitlement>(query)}` : ""}`,
        ...config,
      });
    },
    [],
  );

  const get = useCallback(async (entityId: string, query?: RqlQuery<Entitlement>) => {
    return http<Entitlement>({
      method: "GET",
      url: `${rootPath}/${entityId}${query ? `?${getCustomQueryString<Entitlement>(query)}` : ""}`,
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

  const terminateEntitlement = useCallback(async (entitlementId: string) => {
    return http<Entitlement>({
      method: "POST",
      url: `${rootPath}/${entitlementId}/terminate`,
    });
  }, []);

  const deleteEntitlement = useCallback(async (entitlementId: string) => {
    return http<Entitlement>({
      method: "DELETE",
      url: `${rootPath}/${entitlementId}`,
    });
  }, []);

  return useMemo(
    () => ({ list, get, save, terminateEntitlement, deleteEntitlement }),
    [list, get, save, terminateEntitlement, deleteEntitlement],
  );
}
