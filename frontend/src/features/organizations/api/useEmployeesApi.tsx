import { useMemo } from "react";

import { EmployeeRead } from "@swo/ffc-api-model";

import { AddUserForm } from "~organizations/details/users/modal/AddUserForm.Schema";
import { mockResponse } from "~shared/utils/mockResponse";

// Sandbox: static implementation. `addAdmin` backs the create-user modal;
// the users grid reads mock employees directly via useGridInMemory.
export function useEmployeesApi() {
  return useMemo(
    () => ({
      addAdmin: (_organizationId: string, data: AddUserForm) =>
        mockResponse<EmployeeRead>({
          id: `emp-${Date.now()}`,
          email: data.email,
          display_name: data.display_name,
          created_at: new Date().toISOString(),
          last_login: null,
          roles_count: 1,
        }),
    }),
    [],
  );
}
