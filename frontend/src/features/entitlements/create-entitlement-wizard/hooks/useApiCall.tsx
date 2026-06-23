import { useCallback } from "react";

import { Column, generateRqlQuery } from "@swo/design-system/list";
import { getExpressionBuilder } from "@swo/rql-client";

import { Account } from "~features/entitlements/api/model";
import { useAccountsApi } from "~features/entitlements/api/useAccountsApi";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

export function useApiCall(columns: Column<Account>[]) {
  const { list } = useAccountsApi();

  return useCallback(
    async (filter: string, page: number, limit: number) => {
      const { eq } = getExpressionBuilder<Account>();
      const query = generateRqlQuery(columns, filter, page, limit)
        .addAndOperation(eq("type", "affiliate"))
        .orderBy("name");
      const response = await list(query);

      return mapAxiosResponseDataList(response);
    },
    [columns, list],
  );
}
