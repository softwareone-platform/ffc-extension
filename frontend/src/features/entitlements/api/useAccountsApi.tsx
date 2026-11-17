import { useMemo } from "react";

import { AccountRead } from "~api/ffc-api-model";
import { useEntityApi } from "~shared/hooks/useEntityApi";

const rootPath = "/ops/v1/accounts";

export function useAccountsApi() {
  const { list } = useEntityApi<AccountRead>(rootPath);

  return useMemo(() => ({ list }), [list]);
}
