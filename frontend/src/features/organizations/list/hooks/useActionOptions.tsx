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
      const editEnabledStatus: Set<OrganizationStatus> = new Set(["active", "terminated"]);
      const deleteEnabledStatus: Set<OrganizationStatus> = new Set(["terminated"]);

      return [
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
