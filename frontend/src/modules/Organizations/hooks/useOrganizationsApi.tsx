import { RqlQuery } from "@swo/rql-client";
import { Entity } from "@swo/service";

import { useCallback, useMemo } from "react";
import { http } from "@mpt-extension/sdk";
import { DatasourceRead, EmployeeRead, OrganizationRead } from "@swo/ffc-api-model";
import { AxiosRequestConfig } from "axios";

export interface ListResponse<T> {
  total: number;
  offset?: number;
  limit?: number;
  data?: Array<T>;
}
const rootPath = "/ops/v1/organizations";

export function useOrganizationsApi() {
  const list = useCallback(
    async (
      query: RqlQuery<Entity<OrganizationRead>>,
      config?: AxiosRequestConfig<ListResponse<Entity<OrganizationRead>>>,
    ) => {
      return http<ListResponse<Entity<OrganizationRead>>>({
        method: "GET",
        url: `${rootPath}${query ? `?${query.toString()}` : ""}`,
        ...config,
      });
    },
    [rootPath],
  );

  const get = useCallback(
    async (entityId: string, query?: RqlQuery<OrganizationRead>) => {
      return http<OrganizationRead>({
        method: "GET",
        url: `${rootPath}/${entityId}${query ? `?${query.toString()}` : ""}`,
      });
    },
    [rootPath],
  );

  const listOrganizationEmployees = useCallback(
    async (organizationId: string, query?: RqlQuery<EmployeeRead>) => {
      return http({
        method: "GET",
        url: `${rootPath}/${organizationId}/employees${query ? `?${query.toString()}` : ""}`,
      });
    },
    [rootPath],
  );
  const listOrganizationDataSources = useCallback(
    async (organizationId: string, query?: RqlQuery<DatasourceRead>) => {
      return http({
        method: "GET",
        url: `${rootPath}/${organizationId}/datasources${query ? `?${query.toString()}` : ""}`,
      });
    },
    [rootPath],
  );

  return useMemo(
    () => ({ list, get, listOrganizationEmployees, listOrganizationDataSources }),
    [list, get, listOrganizationEmployees, listOrganizationDataSources],
  );
}
