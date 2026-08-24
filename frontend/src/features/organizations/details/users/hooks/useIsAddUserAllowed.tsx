import { useMemo } from "react";

import type { AccountType, OrganizationStatus } from "~api/ffc-api-model";
import { useOrganizationDetailsApi } from "~features/organizations/api/useOrganizationDetailsApi";
import { useUserRole } from "~shared/hooks/useUserRole";

export function useIsUserAddAllowed(organizationId: string) {
  const { role } = useUserRole();
  const { data: organization } = useOrganizationDetailsApi(organizationId);
  const addUserAllowedRoles: AccountType[] = ["admin", "operations"];
  const addUserAllowedStatuses: OrganizationStatus[] = ["active"];

  const isAddUserAllowed = useMemo(() => {
    const isAddUserAllowedRole = role && addUserAllowedRoles.includes(role);
    const isAddUserAllowedStatus =
      organization && addUserAllowedStatuses.includes(organization?.status);
    return isAddUserAllowedRole && isAddUserAllowedStatus;
  }, [role, organization]);

  return { isAddUserAllowed };
}
