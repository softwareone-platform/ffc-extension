import { useMemo } from "react";

import {
  GridCellSimple,
  GridCellTitleSubtitle,
  GridColumnDefinition,
  GridFieldDefinition,
  GridInMemoryConfig,
  useGridInMemory,
} from "@swo/design-system/grid";
import { EmployeeRead } from "@swo/ffc-api-model";
import { StatusChip } from "@swo/mp-status-chip";
import { Paths } from "@swo/rql-client";

import { mockEmployees } from "~organizations/api/mockData";
import { GridCellDate } from "~shared/components/grid/GridCellDate";
import { useFixedT } from "~shared/hooks/useFixedT";

// Sandbox: client-side grid over static employees. `is_admin` is a UI-only
// flag not present on EmployeeRead, so we derive it here for the demo rows.
type Employee = EmployeeRead & { is_admin: boolean };

type Columns = Array<Omit<GridColumnDefinition<Employee>, "fields"> & { fields: Paths<Employee>[] }>;

const noop = () => {};

export function useGridConfig(_organizationId: string) {
  const tColumns = useFixedT("shared:grid:columns");
  const tFields = useFixedT("shared:grid:fields");

  const data = useMemo<Employee[]>(
    () => mockEmployees.map((e, i) => ({ ...e, is_admin: i === 0 })),
    [],
  );

  const config = useMemo(() => {
    const columns: Columns = [
      {
        name: "email",
        title: tColumns("email"),
        fields: ["email"],
        cell: (item: Employee) => <GridCellSimple>{item.email}</GridCellSimple>,
      },
      {
        name: "user",
        title: tColumns("user"),
        fields: ["display_name", "id"],
        cell: (item: Employee) => (
          <GridCellTitleSubtitle title={item.display_name || item.email} subtitle={item.id} />
        ),
      },
      {
        name: "user_type",
        title: tColumns("userType"),
        fields: ["is_admin"],
        cell: (item: Employee) => (
          <GridCellSimple>
            <StatusChip
              status={item.is_admin ? "Admin" : "User"}
              color={item.is_admin ? "success" : "gray"}
            />
          </GridCellSimple>
        ),
        initialWidth: 150,
      },
      {
        name: "roles_count",
        title: tColumns("rolesCount"),
        fields: ["roles_count"],
        cell: (item: Employee) => <GridCellSimple>{item.roles_count}</GridCellSimple>,
        initialWidth: 150,
      },
      {
        name: "last_login",
        title: tColumns("lastLogin"),
        fields: ["last_login"],
        cell: (item: Employee) => <GridCellDate value={item.last_login} />,
        initialWidth: 150,
      },
      {
        name: "created_at",
        title: tColumns("createdAt"),
        fields: ["created_at"],
        cell: (item: Employee) => <GridCellDate value={item.created_at} />,
        initialWidth: 150,
      },
    ];

    const fields: GridFieldDefinition[] = [
      { title: tFields("id"), name: "id" },
      { title: tFields("email"), name: "email" },
      { title: tFields("displayName"), name: "display_name" },
      { title: tFields("lastLogin"), name: "last_login" },
      { title: tFields("createdAt"), name: "created_at" },
    ];

    return {
      id: "grid__organizations-details-users",
      columns,
      fields,
      isDefaultView: true,
      selectedView: "default",
    } as GridInMemoryConfig<Employee>;
  }, [tColumns, tFields]);

  return { refresh: noop, silentRefresh: noop, ...useGridInMemory(data, config) };
}
