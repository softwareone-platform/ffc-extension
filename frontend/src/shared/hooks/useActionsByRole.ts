import { useCallback } from "react";

import type { ListOption } from "@swo/dropdown";

import { useUserRole } from "~shared/hooks/useUserRole";

export function useActionsByRole<T extends string>(): (
  actions: (ListOption<T> & { requiredRoles?: string[] })[],
) => (ListOption<T> & { requiredRoles?: string[] })[] {
  const { role } = useUserRole();

  return useCallback(
    (
      actions: (ListOption<T> & { requiredRoles?: string[] })[],
    ): (ListOption<T> & { requiredRoles?: string[] })[] => {
      return role
        ? actions.filter((action) => !action.requiredRoles || action.requiredRoles.includes(role))
        : [];
    },
    [role],
  );
}
