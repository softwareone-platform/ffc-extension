import { useCallback } from "react";

import { ListOption } from "@swo/design-system/dropdown";

import { OrganizationRead, OrganizationStatus } from "~api/ffc-api-model";
import { OrganizationAction } from "~features/organizations/api/model";
import { RoleAwareAction, useActionsByRole } from "~shared/hooks/useActionsByRole";
import { useFixedT } from "~shared/hooks/useFixedT";
import { isDeletionAllowed } from "~shared/utils/DateUtils";

export function useActionOptions(): (entity: OrganizationRead) => ListOption<OrganizationAction>[] {
  const tActions = useFixedT("shared:actions");
  const filterActionsByRole = useActionsByRole<OrganizationAction>();
  const now = new Date();

  return useCallback(
    (item: OrganizationRead): ListOption<OrganizationAction>[] => {
      const editEnabledStatus: Set<OrganizationStatus> = new Set(["active", "terminated"]);
      const isDeleteEnabled =
        item.status === "terminated" && isDeletionAllowed(item.events.terminated?.at, now);

      const actions: RoleAwareAction<OrganizationAction>[] = [
        {
          label: tActions("edit"),
          value: "edit",
          isDisabled: !editEnabledStatus.has(item.status!),
          requiredRoles: ["admin"],
        },
        {
          label: tActions("delete"),
          value: "delete",
          isDisabled: !isDeleteEnabled,
          requiredRoles: ["admin"],
          props: { className: "dangerous-option" },
        },
      ];

      return filterActionsByRole(actions);
    },
    [filterActionsByRole, isDeletionAllowed, tActions],
  );
}
