import { useMemo } from "react";

import type { AccountType, OrganizationStatus } from "~api/ffc-api-model";
import { useOrganizationDetailsApi } from "~features/organizations/api/useOrganizationDetailsApi";
import { useUserRole } from "~shared/hooks/useUserRole";

export function useIsUserAddAllowed(organizationId: string) {
  const { role } = useUserRole();
  const { data: organization } = useOrganizationDetailsApi(organizationId);
  const addUserAllowedRoles: Set<AccountType> = new Set(["admin", "operations"]);
  const addUserAllowedStatuses: Set<OrganizationStatus> = new Set(["active"]);

  const isAddUserAllowed = useMemo(() => {
    const isAddUserAllowedRole = role && addUserAllowedRoles.has(role);
    const isAddUserAllowedStatus = organization && addUserAllowedStatuses.has(organization?.status);
    return isAddUserAllowedRole && isAddUserAllowedStatus;
  }, [role, organization]);

  return { isAddUserAllowed };
}
