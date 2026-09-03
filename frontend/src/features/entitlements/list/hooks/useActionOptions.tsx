import { useCallback } from "react";

import { ListOption } from "@swo/design-system/dropdown";

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

      return [
        {
          label: tActions("terminate"),
          value: "terminate",
          isDisabled: !terminateEnabledStatus.has(item.status!),
          props: { className: "dangerous-option" },
        },
        { type: "divider" },
        {
          label: tActions("delete"),
          value: "delete",
          isDisabled: !deleteEnabledStatus.has(item.status!),
          props: { className: "dangerous-option" },
        },
      ];
    },
    [role, tActions],
  );
}
