import { RqlQuery } from "@swo/rql-client";
import { Entity } from "@swo/service";

import { useCallback, useMemo } from "react";
import { http } from "@mpt-extension/sdk";
import { EntitlementRead } from "@swo/ffc-api-model";
import { AxiosRequestConfig } from "axios";

export interface ListResponse<T> {
  total: number;
  offset?: number;
  limit?: number;
  data?: Array<T>;
}
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
    [rootPath],
  );

  const get = useCallback(
    async (entityId: string, query?: RqlQuery<EntitlementRead>) => {
      return http<EntitlementRead>({
        method: "GET",
        url: `${rootPath}/${entityId}${query ? `?${query.toString()}` : ""}`,
      });
    },
    [rootPath],
  );

  return useMemo(
    () => ({ list, get }),
    [list, get],
  );
}
