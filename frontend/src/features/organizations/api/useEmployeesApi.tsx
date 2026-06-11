import { useCallback, useMemo } from "react";

import { AxiosRequestConfig } from "axios";

import { EmployeeRead } from "@swo/ffc-api-model";
import { RqlQuery } from "@swo/rql-client";
import { Entity } from "@swo/service";

import { http } from "@mpt-extension/sdk";

import { AddUserForm } from "~features/modal/user/AddUserForm.Schema";

export interface ListResponse<T> {
  total: number;
  offset?: number;
  limit?: number;
  data?: Array<T>;
}
const rootPath = "/ops/v1/organizations";

export function useEmployeesApi() {
  const list = useCallback(
    async (
      organizationId: string,
      query?: RqlQuery<EmployeeRead>,
      config?: AxiosRequestConfig<ListResponse<Entity<EmployeeRead>>>,
    ) => {
      return http({
        method: "GET",
        url: `${rootPath}/${organizationId}/employees${query ? `?${query.toString()}` : ""}`,
        ...config,
      });
    },
    [],
  );

  const addAdmin = useCallback(async (organizationId: string, data: AddUserForm) => {
    return http<EmployeeRead>({
      method: "POST",
      url: `${rootPath}/${organizationId}/add-admin`,
      data: { ...data, notes: "Add user as admin" },
    });
  }, []);

  return useMemo(() => ({ list, addAdmin }), [list, addAdmin]);
}
