import { useMemo } from "react";

import { GridFieldDefinition } from "@swo/design-system/grid";
import {
  GridCellSimple,
  GridCellTitleSubtitle,
  GridColumnDefinition,
  UseAsyncGridConfig,
  useGridAsync,
} from "@swo/design-system/grid";
import { EmployeeRead } from "@swo/ffc-api-model";
import { StatusChip } from "@swo/mp-status-chip";
import { Paths } from "@swo/rql-client";

import { useOrganizationsApi } from "~organizations/api";
import { GridCellDate } from "~shared/components/grid/GridCellDate";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

type Employee = EmployeeRead & { is_admin: boolean };

type Columns = Array<
  Omit<GridColumnDefinition<Employee>, "fields"> & {
    fields: Paths<Employee>[];
  }
>;

export function useColumns(): Columns {
  const tColumns = useFixedT("shared:grid:columns");

  return useMemo(() => {
    return [
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
        cell: (item: Employee) => (
          // <GridCellSimple>{item.last_login}</GridCellSimple>
          <GridCellDate value={item.last_login} />
        ),
        initialWidth: 150,
      },
      {
        name: "created_at",
        title: tColumns("createdAt"),
        fields: ["created_at"],
        cell: (item: Employee) => <GridCellDate value={item.created_at} />,
        initialWidth: 150,
      },
      {
        name: "actions",
        title: tColumns("actions"),
        fields: [],
        cell: () => <></>,
        initialWidth: 100,
      },
    ];
  }, [tColumns]);
}

export function useFields() {
  const tFields = useFixedT("shared:grid:fields");

  return useMemo(
    (): GridFieldDefinition[] => [
      {
        title: tFields("id"),
        name: "id",
      },
      { title: tFields("email"), name: "email" },
      // { title: tFields("displayName"), name: "display_name" },
      { title: tFields("displayName"), name: "name" }, // temporary until we fix filtering in the backend
      { title: tFields("lastLogin"), name: "last_login" },
      { title: tFields("createdAt"), name: "created_at" },
    ],
    [tFields],
  );
}

export function useAsyncOptions(organizationId: string) {
  const { listOrganizationEmployees } = useOrganizationsApi();
  const baseQueryKey: unknown[] = ["OrganizationUsers", organizationId];
  return useReactQueryRqlGrid<EmployeeRead, Awaited<ReturnType<typeof listOrganizationEmployees>>>(
    baseQueryKey,
    (query) => ({
      queryKey: [baseQueryKey, query.toString(), organizationId],
      queryFn: () => listOrganizationEmployees(organizationId, query),
      select: mapAxiosResponseDataList,
    }),
  );
}

export function useGridConfig(organizationId: string) {
  const columns = useColumns();
  const fields = useFields();
  // const views = useViews();
  const asyncOptions = useAsyncOptions(organizationId);

  const config = useMemo(
    () =>
      ({
        id: "grid__organizations-details-users",
        // memoizeId: 'gridWithRqlStory',
        // views,
        columns,
        fields,
        isDefaultView: true,
        selectedView: "default",
        ...asyncOptions,
      }) as UseAsyncGridConfig<EmployeeRead>,
    [columns, fields, asyncOptions],
  );

  const gridProps = useGridAsync(config);
  return { silentRefresh: asyncOptions.silentRefresh, refresh: asyncOptions.refresh, ...gridProps };
}
