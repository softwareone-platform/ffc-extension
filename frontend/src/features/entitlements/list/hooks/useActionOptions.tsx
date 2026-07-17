import { useCallback } from "react";

import { ListItem, ListOption } from "@swo/dropdown";

import { EntitlementStatus } from "~api/ffc-api-model";
import { Entitlement, EntitlementAction } from "~features/entitlements/api/model";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useUserRole } from "~shared/hooks/useUserRole";

export function useActionOptions(): (entity: Entitlement) => ListOption<EntitlementAction>[] {
  const { role } = useUserRole();
  const tActions = useFixedT("shared:actions");

  const terminateEnabledStatus: EntitlementStatus[] = ["active"];
  const deleteEnabledStatus: EntitlementStatus[] = ["new"];

  return useCallback(
    (item: Entitlement): ListOption<EntitlementAction>[] => {
      const adminActions: ListOption<EntitlementAction>[] = [
        { type: "divider" },
        {
          label: tActions("delete"),
          value: "delete",
          isDisabled: role !== "admin" || !deleteEnabledStatus.includes(item.status!),
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
          isDisabled: !terminateEnabledStatus.includes(item.status!),
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
