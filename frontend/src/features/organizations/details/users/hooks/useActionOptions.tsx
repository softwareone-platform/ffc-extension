import { useCallback } from "react";

import { ListOption } from "@swo/dropdown";

import { Employee, EmployeeActions } from "~features/organizations/api/model";
import { useActionsByRole } from "~shared/hooks/useActionsByRole";
import { useFixedT } from "~shared/hooks/useFixedT";

export function useActionOptions(): (entity: Employee) => ListOption<EmployeeActions>[] {
  const tActions = useFixedT("shared:actions");
  const filterActionsByRole = useActionsByRole<EmployeeActions>();

  return useCallback(
    (item: Employee): ListOption<EmployeeActions>[] => {
      const actions: (ListOption<EmployeeActions> & { requiredRoles?: string[] })[] = [
        {
          label: tActions("make_admin"),
          value: "make_admin",
          isDisabled: item.is_admin,
          requiredRoles: ["admin"],
        },
      ];

      return filterActionsByRole(actions);
    },
    [filterActionsByRole, tActions],
  );
}
