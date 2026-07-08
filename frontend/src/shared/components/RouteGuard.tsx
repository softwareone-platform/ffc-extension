import { PropsWithChildren, useEffect } from "react";

import { AccountType } from "~api/ffc-api-model";
import { useUserRole } from "~shared/hooks/useUserRole";
import { useErrorHandler } from "~shared/providers/ErrorHandlerProvider";

export interface RouteGuardProps extends PropsWithChildren {
  readonly allowedRoles: readonly AccountType[] | AccountType;
}

export function RouteGuard({ children, allowedRoles }: RouteGuardProps) {
  const { role } = useUserRole();
  const { handleError } = useErrorHandler();

  useEffect(() => {
    const roles = typeof allowedRoles === "string" ? [allowedRoles] : allowedRoles;

    if (roles.length > 0 && (!role || !roles.includes(role))) {
      handleError("403", "Access to this module is not allowed for the current user");
    }
  }, [allowedRoles, role]);

  return <>{children}</>;
}
