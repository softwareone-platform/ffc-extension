import { useCallback } from "react";

import { ListOption } from "@swo/dropdown";

import { EntitlementStatus } from "~api/ffc-api-model";
import { Entitlement, EntitlementAction } from "~features/entitlements/api/model";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useUserRole } from "~shared/hooks/useUserRole";

export function useActionOptions(): (entity: Entitlement) => ListOption<EntitlementAction>[] {
  const { role } = useUserRole();
  const tActions = useFixedT("shared:actions");

  return useCallback(
    (item: Entitlement): ListOption<EntitlementAction>[] => {
      const terminateEnabledStatus: Set<EntitlementStatus> = new Set(["active"]);
      const deleteEnabledStatus: Set<EntitlementStatus> = new Set(["new"]);
      const adminActions: ListOption<EntitlementAction>[] = [
        { type: "divider" },
        {
          label: tActions("delete"),
          value: "delete",
          isDisabled: role !== "admin" || !deleteEnabledStatus.has(item.status!),
          props: { className: "dangerous-option" },
        },
      ];
      const redeemAction: ListOption<EntitlementAction>[] = [
        { label: tActions("redeem"), value: "redeem", isDisabled: true },
      ];
      const terminateAction: ListOption<EntitlementAction>[] = [
        {
          label: tActions("terminate"),
          value: "terminate",
          isDisabled: !terminateEnabledStatus.has(item.status!),
          props: { className: "dangerous-option" },
        },
      ];

      return [
        ...(role === "admin" ? redeemAction : []),
        ...(item.status !== "terminated" ? terminateAction : []),
        ...(role === "admin" && item.status !== "deleted" ? adminActions : []),
      ];
    },
    [role, tActions],
  );
}
