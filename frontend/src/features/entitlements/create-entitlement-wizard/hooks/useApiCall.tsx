import { useCallback } from "react";

import { Column, generateRqlQuery } from "@swo/design-system/list";
import { AccountRead } from "@swo/ffc-api-model";
import { getExpressionBuilder } from "@swo/rql-client";

import { useAccountsApi } from "~features/entitlements/api/useAccountsApi";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

// import { mapAxiosResponseDataList } from '@/Modules/Shared/ReactQueryUtils';
// import { useSellersApi } from '@/api/useSellersApi';

export function useApiCall(columns: Column<AccountRead>[]) {
  const { list } = useAccountsApi();

  return useCallback(
    async (filter: string, page: number, limit: number) => {
      const { eq } = getExpressionBuilder<AccountRead>();
      const query = generateRqlQuery(columns, filter, page, limit)
        .addAndOperation(eq("type", "affiliate"))
        .orderBy("name");
      const response = await list(query);

      return mapAxiosResponseDataList(response);
    },
    [columns, list],
  );
}
