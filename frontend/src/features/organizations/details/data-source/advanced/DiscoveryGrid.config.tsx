import { useMemo } from "react";

import {
  GridCellSimple,
  GridColumnDefinition,
  GridInMemoryConfig,
  useGridInMemory,
} from "@swo/design-system/grid";
import { NO_VALUE } from "@swo/design-system/utils";
import { Paths } from "@swo/rql-client";

import { DatasourceDiscoveryItem } from "~api/ffc-api-model";
import { Status } from "~shared/components/entity-status-chip/EntityStatusChip";
import { GridCellDate } from "~shared/components/grid/GridCellDate";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useGridIdentity } from "~shared/hooks/useGridIdentity";
import { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import { isEpoch } from "~shared/utils/DateUtils";

type Columns = Array<
  Omit<GridColumnDefinition<DatasourceDiscoveryItem>, "fields"> & {
    fields: Paths<DatasourceDiscoveryItem>[];
  }
>;

export function useColumns(): Columns {
  const tColumns = useFixedT("shared:grid:columns");
  const tResourceType = useFixedT("shared:grid:resourceType");

  return useMemo(() => {
    return [
      {
        name: "resource_type",
        title: tColumns("resource_type"),
        fields: ["resource_type"],
        cell: (item: DatasourceDiscoveryItem) => (
          <GridCellSimple>{tResourceType(item.resource_type || "unknown")}</GridCellSimple>
        ),
        isFilterable: false,
      },
      {
        name: "last_discovery_at",
        title: tColumns("last_discovery_at"),
        fields: ["last_discovery_at"],
        cell: (item: DatasourceDiscoveryItem) =>
          isEpoch(item.last_discovery_at) ? (
            <GridCellSimple>{NO_VALUE}</GridCellSimple>
          ) : (
            <GridCellDate value={item.last_discovery_at} />
          ),
      },
      {
        name: "status",
        title: tColumns("status"),
        fields: ["status"],
        cell: (item: DatasourceDiscoveryItem) => (
          <GridCellSimple>
            <Status status={item.status}></Status>
          </GridCellSimple>
        ),
      },
    ];
  }, [tColumns, tResourceType]);
}

export function useGridConfig(data: DatasourceDiscoveryItem[]) {
  const columns = useColumns();

  const gridInfoDialogConfig = useGridInfoDialogConfiguration();
  const identity = useGridIdentity("datasource-discovery-details");

  const config = useMemo(
    () =>
      ({
        ...identity,
        columns,
        fields: [],
        isDefaultView: true,
        isToHideToolbar: true,
        selectedView: "default",
        paging: { pageSize: data.length },
        isToHideFooter: true,
        ...gridInfoDialogConfig,
      }) as GridInMemoryConfig<DatasourceDiscoveryItem>,
    [identity, columns, gridInfoDialogConfig, data],
  );

  return useGridInMemory(data, config);
}
