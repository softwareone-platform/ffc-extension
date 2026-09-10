import { useMemo } from "react";

import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { GridFieldDefinition } from "@swo/design-system/grid";
import {
  GridCellSimple,
  GridColumnDefinition,
  UseAsyncGridConfig,
  useGridAsync,
} from "@swo/design-system/grid";
import { NO_VALUE } from "@swo/design-system/utils";
import { Paths } from "@swo/rql-client";

import { DatasourceRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~organizations/api";
import { useOrganizationContext } from "~organizations/providers/OrganizationsProvider";
import DataSourceIcon from "~shared/components/custom-icons/CustomIcon";
import { GridCellCurrency } from "~shared/components/grid/GridCellCurrency";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

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
        name: "id",
        title: tColumns("id"),
        fields: ["id"],
        cell: (item: DatasourceRead) => <GridCellSimple>{item.id}</GridCellSimple>,
        isHidden: true,
      },
      {
        name: "name",
        title: tColumns("dataSource"),
        fields: ["name", "datasource_id"],
        cell: (item: DatasourceRead) => (
          <GridCellSimple>
            <EntityReferenceCell
              primaryContent={item.name}
              secondaryContent={item.datasource_id || ""}
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
        fields: ["parent.id", "parent.name", "parent.type"],
        cell: (item: DatasourceRead) => {
          return item.parent?.id ? (
            <GridCellSimple>
              <EntityReferenceCell
                primaryContent={item.parent?.name}
                secondaryContent={item.parent?.id}
                secondaryContentMaxHeight={50}
                icon={<DataSourceIcon name={item.parent?.type || "unknown"} size={48} />}
              />
            </GridCellSimple>
          ) : (
            <GridCellSimple>{NO_VALUE}</GridCellSimple>
          );
        },
      },
      {
        name: "resources_charged_this_month",
        title: tColumns("resources_charged_this_month"),
        fields: ["resources_charged_this_month"],
        cell: (item: DatasourceRead) => (
          <GridCellCurrency value={item.resources_charged_this_month} currency={""} />
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
  const tValue = useFixedT("shared:grid:dataSourceType");

  return useMemo(
    (): GridFieldDefinition[] => [
      {
        title: tFields("id"),
        name: "id",
      },
      { title: tFields("name"), name: "name" },
      {
        name: "type",
        title: tFields("type"),
        type: "list",
        options: [
          { value: "aws_cnr", label: tValue("aws_cnr") },
          { value: "azure_cnr", label: tValue("azure_cnr") },
          { value: "azure_tenant", label: tValue("azure_tenant") },
          { value: "gcp_cnr", label: tValue("gcp_cnr") },
          { value: "gcp_tenant", label: tValue("gcp_tenant") },
          { value: "unknown", label: tValue("unknown") },
        ],
      },
      { title: tFields("datasourceId"), name: "datasource_id" },
    ],
    [tFields],
  );
}

export function useAsyncOptions(organizationId: string) {
  const { listOrganizationDataSources } = useOrganizationsApi();
  const baseQueryKey: unknown[] = ["OrganizationDataSources"];
  return useReactQueryRqlGrid<
    DatasourceRead,
    Awaited<ReturnType<typeof listOrganizationDataSources>>
  >(baseQueryKey, (query) => ({
    queryKey: [baseQueryKey, query.toString(), organizationId],
    queryFn: () => listOrganizationDataSources(organizationId, query),
    select: mapAxiosResponseDataList,
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
