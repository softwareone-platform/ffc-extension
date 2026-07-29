import { useMemo } from "react";

import { OrganizationRead } from "@swo/ffc-api-model";

import { mockResponse } from "~shared/utils/mockResponse";

import { mockOrganizations } from "./mockData";

// Sandbox: static implementation. `get` backs the organization detail view;
// grids read the mock arrays directly via useGridInMemory, so no list() here.
export function useOrganizationsApi() {
  return useMemo(
    () => ({
      get: (entityId: string, _query?: unknown) =>
        mockResponse<OrganizationRead>(
          mockOrganizations.find((o) => o.id === entityId) ?? mockOrganizations[0],
        ),
    }),
    [],
  );
}
