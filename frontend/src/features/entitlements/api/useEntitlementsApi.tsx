import { useCallback, useMemo } from "react";

import { http } from "@mpt-extension/sdk";

import { EntitlementCreate } from "~api/ffc-api-model";
import { useEntityApi } from "~shared/hooks/useEntityApi";

import { Entitlement } from "./model";

const rootPath = "/ops/v1/entitlements";

export function useEntitlementsApi() {
  const { list, get, save } = useEntityApi<Entitlement, EntitlementCreate>(rootPath);

  const terminateEntitlement = useCallback((entitlementId: string) => {
    return http<Entitlement>({
      method: "POST",
      url: `${rootPath}/${entitlementId}/terminate`,
    });
  }, []);

  const deleteEntitlement = useCallback((entitlementId: string) => {
    return http<Entitlement>({
      method: "DELETE",
      url: `${rootPath}/${entitlementId}`,
    });
  }, []);

  return useMemo(
    () => ({ list, get, save, terminateEntitlement, deleteEntitlement }),
    [list, get, save, terminateEntitlement, deleteEntitlement],
  );
}
