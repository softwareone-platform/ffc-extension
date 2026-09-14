import { useCallback, useMemo } from "react";

import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { GridEvents, GridFieldDefinition } from "@swo/design-system/grid";
import {
  GridCellSimple,
  GridColumnDefinition,
  UseAsyncGridConfig,
  useGridAsync,
} from "@swo/design-system/grid";
import { NO_VALUE } from "@swo/design-system/utils";
import { Paths } from "@swo/rql-client";

import { DatasourceRead } from "~api/ffc-api-model";
import { DatasourceAction } from "~features/organizations/api/model";
import { useOrganizationsApi } from "~organizations/api";
import { useOrganizationContext } from "~organizations/providers/OrganizationsProvider";
import DataSourceIcon from "~shared/components/custom-icons/CustomIcon";
import { GridCellCurrency } from "~shared/components/grid/GridCellCurrency";
import { GridCellDate } from "~shared/components/grid/GridCellDate";
import { GridCellDynamicActions } from "~shared/components/grid/GridCellDynamicActions";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import { useUserRole } from "~shared/hooks/useUserRole";
import { isEpoch } from "~shared/utils/DateUtils";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

import { useActionOptions } from "./hooks/useActionOptions";

type Columns = Array<
  Omit<GridColumnDefinition<DatasourceRead>, "fields"> & {
    fields: Paths<DatasourceRead>[];
  }
>;

export function useColumns(): Columns {
  const tColumns = useFixedT("shared:grid:columns");
  const tDataSourceType = useFixedT("shared:grid:dataSourceType");
  const organization = useOrganizationContext();
  const getActions = useActionOptions();
  const { role } = useUserRole();

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
        fields: ["parent_id", "parent.id", "parent.name", "parent.type"],
        cell: (item: DatasourceRead) => {
          return item.parent && item.parent.id ? (
            <GridCellSimple>
              <EntityReferenceCell
                primaryContent={item.parent?.name}
                secondaryContent={item.parent?.datasource_id || NO_VALUE}
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
      {
        name: "last_import_at",
        title: tColumns("last_import_at"),
        fields: ["last_import_at"],
        cell: (item: DatasourceRead) =>
          isEpoch(item.last_import_at) ? (
            <GridCellSimple>{NO_VALUE}</GridCellSimple>
          ) : (
            <GridCellDate value={item.last_import_at} />
          ),
      },
      {
        name: "actions",
        title: tColumns("actions"),
        fields: [],
        cell: (item: DatasourceRead) => (
          <GridCellDynamicActions<DatasourceRead, DatasourceAction>
            item={item}
            actions={getActions(item)}
          />
        ),
        initialWidth: 100,
        isScalable: false,
        isHidden: role !== "admin",
      },
    ];
  }, [tColumns, tDataSourceType, organization, getActions, role]);
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

export function useGridConfig(
  organizationId: string,
  onAction?: (action: DatasourceAction, item: DatasourceRead, silentRefresh: () => void) => void,
) {
  const columns = useColumns();
  const fields = useFields();
  const asyncOptions = useAsyncOptions(organizationId);
  const gridInfoDialogConfig = useGridInfoDialogConfiguration();

  const onGridActionEvent = useCallback(
    (event: GridEvents) => {
      if (event.type === "RowActionTriggered") {
        onAction?.(
          event.data.action as DatasourceAction,
          event.data.item as DatasourceRead,
          asyncOptions.silentRefresh,
        );
      }
    },
    [asyncOptions.silentRefresh, onAction],
  );

  const config = useMemo(
    () =>
      ({
        id: "grid__organizations-details-data-sources",
        columns,
        fields,
        isDefaultView: true,
        selectedView: "default",
        ...asyncOptions,
        ...gridInfoDialogConfig,
        onEvent: onGridActionEvent,
      }) as UseAsyncGridConfig<DatasourceRead>,
    [columns, fields, asyncOptions, onGridActionEvent],
  );

  const gridProps = useGridAsync(config);
  return {
    silentRefresh: asyncOptions.silentRefresh,
    refresh: asyncOptions.refresh,
    ...gridProps,
  };
}
