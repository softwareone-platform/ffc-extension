import { useCallback, useMemo } from "react";

import { AxiosRequestConfig } from "axios";

import { RqlQuery } from "@swo/rql-client";

import { http } from "@mpt-extension/sdk";

import { AccountRead } from "~api/ffc-api-model";
import { ListResponse } from "~shared/utils/mapAxiosResponseDataList";

const rootPath = "/ops/v1/accounts";

// TODO refactor for shared hooks for entitlements and accounts, since they are very similar
export function useAccountsApi() {
  const list = useCallback(
    async (
      query: RqlQuery<AccountRead>,
      config?: AxiosRequestConfig<ListResponse<AccountRead>>,
    ) => {
      return http<ListResponse<AccountRead>>({
        method: "GET",
        url: `${rootPath}${query ? `?${query.toString()}` : ""}`,
        ...config,
      });
    },
    [],
  );

  return useMemo(() => ({ list }), [list]);
}
