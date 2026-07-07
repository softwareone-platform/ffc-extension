import { PropsWithChildren, useContext, useEffect } from "react";

import { AccountType } from "~api/ffc-api-model";
import { useErrorHandler } from "~shared/providers/ErrorHandlerProvider";
import { UserContext } from "~shared/providers/UserContext";

export interface RouteGuardProps extends PropsWithChildren {
  allowedRoles: readonly AccountType[] | AccountType;
}

export function RouteGuard({ children, allowedRoles }: RouteGuardProps) {
  const user = useContext(UserContext);
  const role = user?.account.type;
  const { handleError } = useErrorHandler();

  useEffect(() => {
    const roles = typeof allowedRoles === "string" ? [allowedRoles] : allowedRoles;
    if (roles.length > 0 && (!role || !roles.includes(role))) {
      handleError("403", "Access to this module is not allowed for the current user");
    }
  }, [allowedRoles, role]);

  return <>{children}</>;
}
