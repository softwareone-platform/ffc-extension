import { useCallback } from "react";

import { ListOption } from "@swo/dropdown";

import { OrganizationRead, OrganizationStatus } from "~api/ffc-api-model";
import { OrganizationAction } from "~features/organizations/api/model";
import { useActionsByRole } from "~shared/hooks/useActionsByRole";
import { useFixedT } from "~shared/hooks/useFixedT";

export function useActionOptions(): (entity: OrganizationRead) => ListOption<OrganizationAction>[] {
  const tActions = useFixedT("shared:actions");
  const filterActionsByRole = useActionsByRole<OrganizationAction>();

  return useCallback(
    (item: OrganizationRead): ListOption<OrganizationAction>[] => {
      const editEnabledStatus: Set<OrganizationStatus> = new Set(["active", "cancelled"]);
      const deleteEnabledStatus: Set<OrganizationStatus> = new Set(["cancelled"]);

      const actions: (ListOption<OrganizationAction> & { requiredRoles?: string[] })[] = [
        {
          label: tActions("edit"),
          value: "edit",
          isDisabled: !editEnabledStatus.has(item.status!),
          requiredRoles: ["admin"],
        },
        {
          label: tActions("delete"),
          value: "delete",
          isDisabled: !deleteEnabledStatus.has(item.status!),
          requiredRoles: ["admin"],
          props: { className: "dangerous-option" },
        },
      ];

      return filterActionsByRole(actions);
    },
    [filterActionsByRole, tActions],
  );
}
