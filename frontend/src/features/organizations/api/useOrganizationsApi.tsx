import { useCallback, useMemo } from "react";

import { AxiosRequestConfig } from "axios";

import { RqlQuery } from "@swo/rql-client";
import { Entity } from "@swo/service";

import { http } from "@mpt-extension/sdk";

import { DatasourceRead, EmployeeRead, OrganizationRead } from "~api/ffc-api-model";
import { getCustomQueryString } from "~shared/utils/rqlHelper";

import { EditOrganizationForm } from "../list/edit-organization-modal/EditOrganization.Schema";

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
        url: rootPath + getCustomQueryString<Entity<OrganizationRead>>(query),
        ...config,
      });
    },
    [],
  );

  const get = useCallback(async (entityId: string, query?: RqlQuery<OrganizationRead>) => {
    return http<OrganizationRead>({
      method: "GET",
      url: `${rootPath}/${entityId}` + getCustomQueryString<OrganizationRead>(query),
    });
  }, []);

  const deleteOrganization = useCallback(async (entityId: string) => {
    return http<OrganizationRead>({
      method: "DELETE",
      url: `${rootPath}/${entityId}`,
    });
  }, []);

  const editOrganization = useCallback(async (entityId: string, data: EditOrganizationForm) => {
    return http<OrganizationRead>({
      method: "PUT",
      url: `${rootPath}/${entityId}`,
      data: { name: data.name },
    });
  }, []);

  const listOrganizationEmployees = useCallback(
    async (organizationId: string, query?: RqlQuery<EmployeeRead>) => {
      return http({
        method: "GET",
        url: `${rootPath}/${organizationId}/employees` + getCustomQueryString<EmployeeRead>(query),
      });
    },
    [],
  );
  const listOrganizationDataSources = useCallback(
    async (organizationId: string, query?: RqlQuery<DatasourceRead>) => {
      return http({
        method: "GET",
        url:
          `${rootPath}/${organizationId}/datasources` + getCustomQueryString<DatasourceRead>(query),
      });
    },
    [],
  );

  return useMemo(
    () => ({
      list,
      get,
      editOrganization,
      deleteOrganization,
      listOrganizationEmployees,
      listOrganizationDataSources,
    }),
    [
      list,
      get,
      editOrganization,
      deleteOrganization,
      listOrganizationEmployees,
      listOrganizationDataSources,
    ],
  );
}
