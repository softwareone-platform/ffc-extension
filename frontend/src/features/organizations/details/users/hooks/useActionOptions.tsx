import { useCallback } from "react";

import { ListOption } from "@swo/dropdown";

import { Employee, EmployeeActions } from "~features/organizations/api/model";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useUserRole } from "~shared/hooks/useUserRole";

export function useActionOptions(): (entity: Employee) => ListOption<EmployeeActions>[] {
  const { role } = useUserRole();
  const tActions = useFixedT("shared:actions");

  return useCallback(
    (item: Employee): ListOption<EmployeeActions>[] => {
      return [
        {
          label: tActions("make_admin"),
          value: "make_admin",
          isDisabled: item.is_admin || role !== "admin",
        },
      ];
    },
    [role, tActions],
  );
}
