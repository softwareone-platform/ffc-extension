import { useCallback } from "react";

import { ListOption } from "@swo/dropdown";

import { OrganizationRead, OrganizationStatus } from "~api/ffc-api-model";
import { OrganizationAction } from "~features/organizations/api/model";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useUserRole } from "~shared/hooks/useUserRole";

export function useActionOptions(): (entity: OrganizationRead) => ListOption<OrganizationAction>[] {
  const { role } = useUserRole();
  const tActions = useFixedT("shared:actions");

  return useCallback(
    (item: OrganizationRead): ListOption<OrganizationAction>[] => {
      const activateEnabledStatus: Set<OrganizationStatus> = new Set(["cancelled"]);
      const terminateEnabledStatus: Set<OrganizationStatus> = new Set(["active"]);
      const editEnabledStatus: Set<OrganizationStatus> = new Set(["active", "cancelled"]);
      const deleteEnabledStatus: Set<OrganizationStatus> = new Set(["cancelled"]);

      return [
        {
          label: tActions("activate"),
          value: "activate",
          isDisabled: !activateEnabledStatus.has(item.status!) || role !== "admin",
        },
        {
          label: tActions("terminate"),
          value: "terminate",
          isDisabled: !terminateEnabledStatus.has(item.status!) || role !== "admin",
          props: { className: "dangerous-option" },
        },
        { type: "divider" },
        {
          label: tActions("edit"),
          value: "edit",
          isDisabled: !editEnabledStatus.has(item.status!) || role !== "admin",
        },
        {
          label: tActions("delete"),
          value: "delete",
          isDisabled: !deleteEnabledStatus.has(item.status!) || role !== "admin",
          props: { className: "dangerous-option" },
        },
      ];
    },
    [role, tActions],
  );
}
