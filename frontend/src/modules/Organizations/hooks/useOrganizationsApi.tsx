import { RqlQuery } from "@swo/rql-client";
import { Entity } from "@swo/service";

import { useCallback, useMemo } from "react";
import { http } from "@mpt-extension/sdk";
import { OrganizationRead } from "@swo/ffc-api-model";
import { CallApiParams } from "@swo/design-system/grid";
import { AxiosRequestConfig } from "axios";

export interface ListResponse<T> {
  total: number;
  offset?: number;
  limit?: number;
  data?: Array<T>;
}
const rootPath = "/ops/v1/organizations";

export function useOrganizationsApi() {
  //   const ORG_URL = `/ops/v1/organizations?${query}`;
  const list = useCallback(
    async (
      query: RqlQuery<Entity<OrganizationRead>>,
      config?: AxiosRequestConfig<ListResponse<Entity<OrganizationRead>>>,
    ) => {
      //   const response = await http<ListResponse<OrganizationRead>>({
      //     method: "GET",
      //     url: `${rootPath}${query ? `?${query.toString()}` : ""}`,
      //     signal: controller?.signal,
      //   });

      return http<ListResponse<Entity<OrganizationRead>>>({
        method: "GET",
        url: `${rootPath}${query ? `?${query.toString()}` : ""}`,
        // `${rootPath}${query ? `?${query.toString()}` : ""}`,
        ...config,
      });

      // if (response.status > 300) {
      //   throw new Error("Failed to fetch data");
      // }

      // const { items, total } = response.data;

      // return { data: items, total };
    },
    [rootPath],
  );

  const get = useCallback(
    async (entityId: string, query?: RqlQuery<Entity<OrganizationRead>>) => {
      return  http<ListResponse<Entity<OrganizationRead>>>({
        method: "GET",
        url: `${rootPath}/${entityId}${query ? `?${query.toString()}` : ""}`,
      });
    },
    [rootPath],
  );

  return useMemo(() => ({ list, get }), [list, get]);
}
