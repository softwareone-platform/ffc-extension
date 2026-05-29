import { useMemo } from "react";

import { Link } from "react-router-dom";

import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { GridFieldDefinition } from "@swo/design-system/grid";
import {
  GridCellSimple,
  GridCellTitleSubtitle,
  GridColumnDefinition,
  UseAsyncGridConfig,
  useGridAsync,
} from "@swo/design-system/grid";
import { EntitlementRead } from "@swo/ffc-api-model";
import { Paths } from "@swo/rql-client";

import { useEntitlementsApi } from "~entitlements/api";
import DataSourceIcon from "~shared/components/data-source-icons/DataSourceIcon";
import { Status } from "~shared/components/entity-status-chip/EntityStatusChip";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

type Columns = Array<
  Omit<GridColumnDefinition<EntitlementRead>, "fields"> & {
    fields: Paths<EntitlementRead>[];
  }
>;

export function useColumns(): Columns {
  const tColumns = useFixedT("shared:grid:columns");

  return useMemo(() => {
    return [
      {
        name: "name",
        title: tColumns("entitlement"),
        fields: ["name", "id"],
        cell: (item: EntitlementRead) => (
          <GridCellTitleSubtitle
            title={<Link to={`${item.id}/general`}>{item.name}</Link>}
            subtitle={item.id}
          />
          // <GridCellTitleSubtitle title={item.name} subtitle={item.id} />
        ),
        initialWidth: 350,
      },
      {
        name: "affiliate_external_id",
        title: tColumns("affiliate_external_id"),
        fields: ["affiliate_external_id"],
        cell: (item: EntitlementRead) => (
          // <GridCellSimple>{item.affiliate_external_id}</GridCellSimple>

          <GridCellTitleSubtitle title={item.owner.name} subtitle={item.owner.id} />
        ),
        initialWidth: 150,
      },

      {
        name: "data_source",
        title: tColumns("data_source"),
        fields: ["linked_datasource_name", "linked_datasource_id", "linked_datasource_type"],
        cell: (item: EntitlementRead) => (
          <GridCellSimple>
            {item.linked_datasource_id && (
              <EntityReferenceCell
                primaryContent={item.linked_datasource_name as string}
                secondaryContent={item.linked_datasource_id as string}
                secondaryContentMaxHeight={50}
                icon={<DataSourceIcon name={item.linked_datasource_type as string} size={48} />}
              />
            )}
          </GridCellSimple>
        ),
        initialWidth: 250,
      },
      {
        name: "organization",
        title: tColumns("organization"),
        fields: [],
        cell: (item: EntitlementRead) => (
          <>
            {item.events.redeemed && (
              <GridCellTitleSubtitle
                title={item.events.redeemed?.by.name}
                subtitle={item.events.redeemed?.by.id}
              />
            )}
          </>
        ),
        initialWidth: 150,
      },
      {
        name: "status",
        title: tColumns("status"),
        fields: ["status"],
        cell: (item: EntitlementRead) => (
          <GridCellSimple>
            <Status<EntitlementRead> item={item}></Status>
          </GridCellSimple>
        ),
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
      { title: tFields("entitlement"), name: "name" },
      {
        title: tFields("affiliate_external_id"),
        name: "affiliate_external_id",
      },
    ],
    [tFields],
  );
}

export function useAsyncOptions() {
  const { list } = useEntitlementsApi();
  const baseQueryKey: unknown[] = ["EntitlementsList"];
  return useReactQueryRqlGrid<EntitlementRead, Awaited<ReturnType<typeof list>>>(
    baseQueryKey,
    (query) => ({
      queryKey: [baseQueryKey, query.toString()],
      queryFn: () => list(query),
      select: mapAxiosResponseDataList<EntitlementRead>,
    }),
  );
}

export function useGridConfig() {
  const columns = useColumns();
  const fields = useFields();
  // const views = useViews();
  const asyncOptions = useAsyncOptions();

  const config = useMemo(
    () =>
      ({
        id: "grid__entitlements-details-users",
        // memoizeId: 'gridWithRqlStory',
        // views,
        columns,
        fields,
        isDefaultView: true,
        selectedView: "default",
        ...asyncOptions,
      }) as UseAsyncGridConfig<EntitlementRead>,
    [columns, fields, asyncOptions],
  );

  const gridProps = useGridAsync(config);
  return { silentRefresh: asyncOptions.silentRefresh, ...gridProps };
}
