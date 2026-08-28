import { useQuery } from "@tanstack/react-query";

import { RqlQuery } from "@swo/rql-client";
import { Entity } from "@swo/service";

import { OrganizationRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~organizations/api";
import { useUserRole } from "~shared/hooks/useUserRole";

// Enough to populate a filter without paging; revisit if tenants exceed this.
const OPTIONS_LIMIT = 200;

export function useOrganizationOptionsApi() {
  const { list } = useOrganizationsApi();
  const { role } = useUserRole();

  return useQuery({
    queryKey: ["Dashboard", "OrganizationOptions"] as const,
    // /ops/v1/organizations is admin/operations only (see Organizations.tsx allowedRoles),
    // so skip the request entirely for affiliates rather than let it 403.
    enabled: role === "admin" || role === "operations",
    queryFn: async () => {
      const response = await list(
        new RqlQuery<Entity<OrganizationRead>>().paging(0, OPTIONS_LIMIT),
      );

      // `list` is declared as returning Entity<OrganizationRead>, but the endpoint sends
      // plain payloads and nothing wraps them. The organizations grid relies on the same
      // thing — its cells are typed `(item: OrganizationRead)`.
      return (response.data.data ?? []) as unknown as OrganizationRead[];
    },
  });
}
