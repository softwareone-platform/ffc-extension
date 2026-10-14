import { useCallback, useMemo } from "react";

import { RqlQuery } from "@swo/rql-client";

import { http } from "@mpt-extension/sdk";

import {
  DatasourceForceReimport,
  DatasourceRead,
  EmployeeRead,
  OrganizationRead,
} from "~api/ffc-api-model";
import { useEntityApi } from "~shared/hooks/useEntityApi";
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
  const { get, list, remove: deleteOrganization } = useEntityApi<OrganizationRead>(rootPath);

  const editOrganization = useCallback((entityId: string, data: EditOrganizationForm) => {
    return http<OrganizationRead>({
      method: "PUT",
      url: `${rootPath}/${entityId}`,
      data: { name: data.name },
    });
  }, []);

  const listOrganizationEmployees = useCallback(
    (organizationId: string, query?: RqlQuery<EmployeeRead>) => {
      return http({
        method: "GET",
        url: `${rootPath}/${organizationId}/employees` + getCustomQueryString<EmployeeRead>(query),
      });
    },
    [],
  );
  const listOrganizationDataSources = useCallback(
    (organizationId: string, query?: RqlQuery<DatasourceRead>) => {
      return http({
        method: "GET",
        url:
          `${rootPath}/${organizationId}/datasources` + getCustomQueryString<DatasourceRead>(query),
      });
    },
    [],
  );

  const forceReimportDatasource = useCallback(
    (organizationId: string, datasourceId: string, data?: DatasourceForceReimport) => {
      return http<void>({
        method: "POST",
        url: `${rootPath}/${organizationId}/datasources/${datasourceId}/force-reimport`,
        data,
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
      forceReimportDatasource,
    }),
    [
      list,
      get,
      editOrganization,
      deleteOrganization,
      listOrganizationEmployees,
      listOrganizationDataSources,
      forceReimportDatasource,
    ],
  );
}
