import { DatasourceRead } from '@swo/ffc-api-model';
import { EntityReferenceCell } from '@swo/design-system/entity-reference-cell';
import { GridFieldDefinition } from '@swo/design-system/grid';
import { Paths } from '@swo/rql-client';
import { useMemo } from 'react';
import DataSourceIcon from "~shared/components/data-source-icons/DataSourceIcon";
import { GridCellCurrency } from "~shared/components/grid/GridCellCurrency";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useOrganizationContext } from "~organizations/providers/OrganizationsProvider";
import { useOrganizationsApi } from "~organizations/api";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import {
  GridCellSimple,
  GridColumnDefinition,
  UseAsyncGridConfig,
  useGridAsync,
} from "@swo/design-system/grid";

type Columns = Array<
  Omit<GridColumnDefinition<DatasourceRead>, "fields"> & {
    fields: Paths<DatasourceRead>[];
  }
>;

export function useColumns(): Columns {
  const tColumns = useFixedT("shared:grid:columns");
  const tDataSourceType = useFixedT("shared:grid:dataSourceType");
  const organization = useOrganizationContext();

  return useMemo(() => {
    return [
      {
        name: "name",
        title: tColumns("dataSource"),
        fields: ["name"],
        cell: (item: DatasourceRead) => (
          <GridCellSimple>
            <EntityReferenceCell
              primaryContent={item.name}
              secondaryContent={item.id}
              secondaryContentMaxHeight={50}
              icon={<DataSourceIcon name={item.type} size={48} />}
            />
          </GridCellSimple>
        ),
      },
      {
        name: "type",
        title: tColumns("type"),
        fields: ["type"],
        cell: (item: DatasourceRead) => (
          <GridCellSimple>{tDataSourceType(item.type)}</GridCellSimple>
        ),
      },
      {
        name: "parent_id",
        title: tColumns("parent_id"),
        fields: ["parent_id"],
        cell: (item: DatasourceRead) => (
          <GridCellSimple>{item.parent_id}</GridCellSimple>
        ),
      },
      {
        name: "resources_charged_this_month",
        title: tColumns("resources_charged_this_month"),
        fields: ["resources_charged_this_month"],
        cell: (item: DatasourceRead) => (
          <GridCellCurrency
            value={item.resources_charged_this_month}
            currency={""}
          />
        ),
      },
      {
        name: "expenses_so_far_this_month",
        title: tColumns("expenses_so_far_this_month"),
        fields: ["expenses_so_far_this_month"],
        cell: (item: DatasourceRead) => (
          <GridCellCurrency
            value={item.expenses_so_far_this_month}
            currency={organization?.currency || ""}
          />
        ),
      },
      {
        name: "expenses_forecast_this_month",
        title: tColumns("expenses_forecast_this_month"),
        fields: ["expenses_forecast_this_month"],
        cell: (item: DatasourceRead) => (
          <GridCellCurrency
            value={item.expenses_forecast_this_month}
            currency={organization?.currency || ""}
          />
        ),
      },
    ];
  }, [tColumns, tDataSourceType, organization]);
}

export function useFields() {
  const tFields = useFixedT("shared:grid:fields");

  return useMemo(
    (): GridFieldDefinition[] => [
      {
        title: tFields("id"),
        name: "id",
      },
      { title: tFields("name"), name: "name" },
      { title: tFields("type"), name: "type" },
    ],
    [tFields],
  );
}

export function useAsyncOptions(organizationId: string) {
  const { listOrganizationDataSources } = useOrganizationsApi();
  const baseQueryKey: any = "OrganizationDataSources";
  return useReactQueryRqlGrid<
    DatasourceRead,
    Awaited<ReturnType<typeof listOrganizationDataSources>>
  >(baseQueryKey, (query) => ({
    queryKey: [baseQueryKey, query.toString(), organizationId],
    queryFn: () => listOrganizationDataSources(organizationId, query),
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
        id: "grid__organizations-details-data-sources",
        // memoizeId: 'gridWithRqlStory',
        // views,
        columns,
        fields,
        isDefaultView: true,
        selectedView: "default",
        ...asyncOptions,
      }) as UseAsyncGridConfig<DatasourceRead>,
    [columns, fields, asyncOptions],
  );

  const gridProps = useGridAsync(config);
  return { silentRefresh: asyncOptions.silentRefresh, ...gridProps };
}
