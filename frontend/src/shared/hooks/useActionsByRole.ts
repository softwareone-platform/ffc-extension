import { useCallback } from "react";

import type { ListOption } from "@swo/design-system/dropdown";

import { useUserRole } from "~shared/hooks/useUserRole";

export type RoleAwareAction<T> = ListOption<T> & {
  requiredRoles?: string[];
};

export type ActionsByRole<T extends string> = (
  actions: RoleAwareAction<T>[],
) => RoleAwareAction<T>[];

export function useActionsByRole<T extends string>(): ActionsByRole<T> {
  const { role } = useUserRole();

  return useCallback(
    (actions: RoleAwareAction<T>[]): RoleAwareAction<T>[] => {
      return role
        ? actions.filter((action) => !action.requiredRoles || action.requiredRoles.includes(role))
        : [];
    },
    [role],
  );
}
