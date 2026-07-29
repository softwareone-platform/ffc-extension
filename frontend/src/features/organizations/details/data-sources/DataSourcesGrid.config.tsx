import { useMemo } from "react";

import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import {
  GridCellSimple,
  GridColumnDefinition,
  GridFieldDefinition,
  GridInMemoryConfig,
  useGridInMemory,
} from "@swo/design-system/grid";
import { DatasourceRead } from "@swo/ffc-api-model";
import { Paths } from "@swo/rql-client";

import { mockDataSources } from "~organizations/api/mockData";
import { useOrganizationContext } from "~organizations/providers/OrganizationsProvider";
import DataSourceIcon from "~shared/components/custom-icons/CustomIcon";
import { GridCellCurrency } from "~shared/components/grid/GridCellCurrency";
import { useFixedT } from "~shared/hooks/useFixedT";

// Sandbox: client-side grid over static data sources.
type Columns = Array<
  Omit<GridColumnDefinition<DatasourceRead>, "fields"> & { fields: Paths<DatasourceRead>[] }
>;

const noop = () => {};

export function useGridConfig(_organizationId: string) {
  const tColumns = useFixedT("shared:grid:columns");
  const tFields = useFixedT("shared:grid:fields");
  const tDataSourceType = useFixedT("shared:grid:dataSourceType");
  const organization = useOrganizationContext();

  const config = useMemo(() => {
    const columns: Columns = [
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
        cell: (item: DatasourceRead) => <GridCellSimple>{tDataSourceType(item.type)}</GridCellSimple>,
      },
      {
        name: "parent_id",
        title: tColumns("parent_id"),
        fields: ["parent_id"],
        cell: (item: DatasourceRead) => <GridCellSimple>{item.parent_id}</GridCellSimple>,
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

    const fields: GridFieldDefinition[] = [
      { title: tFields("id"), name: "id" },
      { title: tFields("name"), name: "name" },
      { title: tFields("type"), name: "type" },
    ];

    return {
      id: "grid__organizations-details-data-sources",
      columns,
      fields,
      isDefaultView: true,
      selectedView: "default",
    } as GridInMemoryConfig<DatasourceRead>;
  }, [tColumns, tDataSourceType, tFields, organization]);

  return { silentRefresh: noop, ...useGridInMemory(mockDataSources, config) };
}
