import { useMemo } from "react";

import { mockResponse } from "~shared/utils/mockResponse";

import { mockAccounts } from "./mockData";

// Sandbox: static implementation matching the real API hook signature.
export function useAccountsApi() {
  return useMemo(
    () => ({
      list: (_query?: unknown) => mockResponse({ total: mockAccounts.length, items: mockAccounts }),
    }),
    [],
  );
}
