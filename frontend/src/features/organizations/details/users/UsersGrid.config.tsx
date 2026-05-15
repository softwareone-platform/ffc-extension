import { EmployeeRead } from "@swo/ffc-api-model";
import { GridCellDate } from "~shared/components/grid/GridCellDate";
import { GridFieldDefinition } from "@swo/design-system/grid";
import { Paths } from "@swo/rql-client";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useMemo } from "react";
import { useOrganizationsApi } from "~organizations/api";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import {
  GridCellSimple,
  GridCellTitleSubtitle,
  GridColumnDefinition,
  UseAsyncGridConfig,
  useGridAsync,
} from "@swo/design-system/grid";
// import { useAsyncOptions } from "~organizations/hooks/useAsyncOptions";

// import { useViews } from "~organizations/hooks/useViews";

const defaultFilter = {
  operator: "and",
  value: [{ operator: "eq", field: "status", value: "active" }],
};
const sort = [{ field: "event.created.at", direction: "desc" }];

type Columns = Array<
  Omit<GridColumnDefinition<EmployeeRead>, "fields"> & {
    fields: Paths<EmployeeRead>[];
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
        cell: (item: EmployeeRead) => (
          <GridCellSimple>{item.email}</GridCellSimple>
        ),
      },
      {
        name: "user",
        title: tColumns("user"),
        fields: ["display_name", "id"],
        cell: (item: EmployeeRead) => (
          <GridCellTitleSubtitle
            title={item.display_name || item.email}
            subtitle={item.id}
          />
        ),
      },
      {
        name: "roles_count",
        title: tColumns("rolesCount"),
        fields: ["roles_count"],
        cell: (item: EmployeeRead) => (
          <GridCellSimple>{item.roles_count}</GridCellSimple>
        ),
        initialWidth: 150,
      },
      {
        name: "last_login",
        title: tColumns("lastLogin"),
        fields: ["last_login"],
        cell: (item: EmployeeRead) => (
          // <GridCellSimple>{item.last_login}</GridCellSimple>
          <GridCellDate value={item.last_login} />
        ),
        initialWidth: 150,
      },
      {
        name: "created_at",
        title: tColumns("createdAt"),
        fields: ["created_at"],
        cell: (item: EmployeeRead) => <GridCellDate value={item.created_at} />,
        initialWidth: 150,
      },
      {
        name: "actions",
        title: tColumns("actions"),
        fields: [],
        cell: (item: EmployeeRead) => <></>,
        initialWidth: 100,
      },
    ];
  }, []);
}

export function useFields() {
  const tColumns = useFixedT("shared:grid:columns");
  const tFields = useFixedT("shared:grid:fields");

  return useMemo(
    (): GridFieldDefinition[] => [
      {
        title: tFields("id"),
        name: "id",
      },
      { title: tFields("email"), name: "email" },
      { title: tFields("displayName"), name: "display_name" },
      { title: tFields("lastLogin"), name: "last_login" },
      { title: tFields("createdAt"), name: "created_at" },
    ],
    [tFields],
  );
}

export function useAsyncOptions(organizationId: string) {
  const { listOrganizationEmployees } = useOrganizationsApi();
  const baseQueryKey: any = "OrganizationUsers";
  return useReactQueryRqlGrid<
    EmployeeRead,
    Awaited<ReturnType<typeof listOrganizationEmployees>>
  >(baseQueryKey, (query) => ({
    queryKey: [baseQueryKey, query.toString(), organizationId],
    queryFn: () => listOrganizationEmployees(organizationId, query),
    select: (res) => {
      return { data: res.data, total: undefined };
    },
  }));
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
    [columns, defaultFilter, sort, fields, asyncOptions],
  );

  const gridProps = useGridAsync(config);
  return { silentRefresh: asyncOptions.silentRefresh, ...gridProps };
}
