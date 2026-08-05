import { useCallback } from "react";

import { Column, generateRqlQuery } from "@swo/design-system/list";
import { getExpressionBuilder } from "@swo/rql-client";

import { Account } from "~features/entitlements/api/model";
import { useAccountsApi } from "~features/entitlements/api/useAccountsApi";
import { useUserRole } from "~shared/hooks/useUserRole";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

export function useApiCall(columns: Column<Account>[]) {
  const { list } = useAccountsApi();
  const { user, role } = useUserRole();

  return useCallback(
    async (filter: string, page: number, limit: number) => {
      if (role === "affiliate") {
        // If the user is an affiliate, we only want to return their own account, so we create a promise that resolves with their account data.
        // This is temporary solution.
         return new Promise<{ data: Account[]; total: number }>((resolve) => {
          setTimeout(() => {
            resolve({
              data: [user?.account as Account],
              total: 1,
            });
          }, 0);
        });
      }

      const { eq } = getExpressionBuilder<Account>();
      const query = generateRqlQuery(columns, filter, page, limit)
        .addAndOperation(eq("type", "affiliate"))
        .orderBy("name");
      const response = await list(query);

      return mapAxiosResponseDataList(response);
    },
    [columns, list, role, user?.account],
  );
}
