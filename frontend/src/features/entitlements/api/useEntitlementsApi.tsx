import { useMemo } from "react";

import { EntitlementCreate } from "@swo/ffc-api-model";

import { mockResponse } from "~shared/utils/mockResponse";

import { mockEntitlements } from "./mockData";
import { Entitlement } from "./model";

// Sandbox: static implementation. `get` backs the detail view and `save` the
// create wizard; the list grid reads mock entitlements via useGridInMemory.
export function useEntitlementsApi() {
  return useMemo(
    () => ({
      get: (entityId: string, _query?: unknown) =>
        mockResponse<Entitlement>(
          mockEntitlements.find((e) => e.id === entityId) ?? mockEntitlements[0],
        ),
      save: (entity: EntitlementCreate) =>
        mockResponse<EntitlementCreate & { id?: string }>({
          ...entity,
          id: `ent-${Date.now()}`,
        }),
    }),
    [],
  );
}
