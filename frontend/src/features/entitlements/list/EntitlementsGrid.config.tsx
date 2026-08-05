import { useCallback, useMemo } from "react";

import { Link } from "react-router-dom";

import { EntityReference } from "@swo/design-system/entity-reference";
import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import {
  GridCellActions,
  GridCellSimple,
  GridCellTitleSubtitle,
  GridColumnDefinition,
  GridEvents,
  GridFieldDefinition,
  UseAsyncGridConfig,
  useGridAsync,
} from "@swo/design-system/grid";
import { getStatusLabel } from "@swo/mp-status-chip";
import { Paths } from "@swo/rql-client";

import { useEntitlementsApi } from "~entitlements/api";
import CustomIcon from "~shared/components/custom-icons/CustomIcon";
import { Status } from "~shared/components/entity-status-chip/EntityStatusChip";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

import { Entitlement, EntitlementAction } from "../api/model";
import { useActionOptions } from "./hooks/useActionOptions";

type Columns = Array<
  Omit<GridColumnDefinition<Entitlement>, "fields"> & {
    fields: Paths<Entitlement>[];
  }
>;

export function useColumns(): Columns {
  const tColumns = useFixedT("shared:grid:columns");
  const getActions = useActionOptions();

  return useMemo(() => {
    return [
      {
        name: "name",
        title: tColumns("entitlement"),
        fields: ["id", "name"],
        cell: (item: Entitlement) => (
          <GridCellTitleSubtitle
            title={<Link to={`${item.id}/general`}>{item.name}</Link>}
            subtitle={item.id}
          />
        ),
        initialWidth: 350,
      },
      {
        name: "affiliate",
        title: tColumns("affiliate"),
        fields: [
          "owner.id",
          "owner.name",
          "owner.external_id",
          "owner.integration",
          "affiliate_external_id",
        ],
        cell: (item: Entitlement) => (
          <GridCellSimple>
            <EntityReference
              primaryContent={item.owner.name}
              secondaryContent={item.owner.id}
              isPrimaryContentBold={false}
              icon={<CustomIcon name={item.owner.integration} size={44} />}
            />
          </GridCellSimple>
        ),
        initialWidth: 150,
      },

      {
        name: "data_source",
        title: tColumns("data_source"),
        fields: ["linked_datasource_name", "linked_datasource_id", "linked_datasource_type"],
        cell: (item: Entitlement) => (
          <GridCellSimple>
            {item.linked_datasource_id && (
              <EntityReferenceCell
                primaryContent={item.linked_datasource_name as string}
                secondaryContent={item.linked_datasource_id as string}
                secondaryContentMaxHeight={50}
                icon={<CustomIcon name={item.linked_datasource_type as string} size={44} />}
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
        cell: (item: Entitlement) => (
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
        cell: (item: Entitlement) => (
          <GridCellSimple>
            <Status<Entitlement> item={item}></Status>
          </GridCellSimple>
        ),
        initialWidth: 100,
      },
      {
        name: "actions",
        title: tColumns("actions"),
        fields: [],
        cell: (item: Entitlement) => <GridCellActions item={item} actions={getActions(item)} />,
        initialWidth: 100,
        type: "Actions",
        isScalable: false,
      },
    ];
  }, [tColumns, getActions]);
}

export function useFields() {
  const tFields = useFixedT("shared:grid:fields");

  return useMemo(
    (): GridFieldDefinition[] => [
      {
        title: tFields("entitlement:id"),
        name: "id",
      },
      { title: tFields("entitlement:name"), name: "name" },
      { title: tFields("affiliate:name"), name: "owner.name" },
      { title: tFields("affiliate:id"), name: "owner.id" },
      {
        title: tFields("affiliate_external_id"),
        name: "affiliate_external_id",
      },
      {
        title: tFields("created_at"),
        name: "events.created.at",
      },
      {
        name: "status",
        title: tFields("status"),
        type: "list",
        options: [
          { value: "active", label: getStatusLabel("Active") },
          { value: "new", label: getStatusLabel("New") },
          { value: "terminated", label: getStatusLabel("Terminated") },
          { value: "deleted", label: getStatusLabel("Deleted") },
        ],
      },
    ],
    [tFields],
  );
}

export function useViews() {
  const tView = useFixedT("shared:grid:views");

  return useMemo(() => {
    return [
      {
        name: "active",
        title: tView("activeEntitlements"),
        configuration: {
          filters: {
            operator: "or",
            value: [
              { operator: "eq", field: "status", value: "active" },
              { operator: "eq", field: "status", value: "new" },
            ],
          },
          sort: [
            { field: "events.created.at", direction: "desc" },
            { field: "status", direction: "desc" },
          ],
        },
      },
      {
        name: "inactive",
        title: tView("inactiveEntitlements"),
        configuration: {
          filters: {
            operator: "or",
            value: [
              { operator: "eq", field: "status", value: "deleted" },
              { operator: "eq", field: "status", value: "terminated" },
            ],
          },
          sort: [
            { field: "events.created.at", direction: "desc" },
            { field: "status", direction: "asc" },
          ],
        },
      },
      {
        name: "all",
        title: tView("allEntitlements"),
        configuration: {
          filters: {},
          sort: [{ field: "events.created.at", direction: "desc" }],
        },
      },
    ];
  }, [tView]);
}

export function useAsyncOptions() {
  const { list } = useEntitlementsApi();
  const baseQueryKey: unknown[] = ["EntitlementsList"];
  return useReactQueryRqlGrid<Entitlement, Awaited<ReturnType<typeof list>>>(
    baseQueryKey,
    (query) => ({
      queryKey: [baseQueryKey, query.toString()],
      queryFn: () => list(query),
      select: mapAxiosResponseDataList<Entitlement>,
    }),
  );
}

export function useGridConfig(
  onAction?: (action: EntitlementAction, item: Entitlement, silentRefresh: () => void) => void,
) {
  const columns = useColumns();
  const fields = useFields();
  const views = useViews();
  const asyncOptions = useAsyncOptions();

  const onGridActionEvent = useCallback(
    (event: GridEvents) => {
      if (event.type === "RowActionTriggered") {
        onAction?.(
          event.data.action as EntitlementAction,
          event.data.item as Entitlement,
          asyncOptions.silentRefresh,
        );
      }
    },
    [asyncOptions.silentRefresh, onAction],
  );

  const config = useMemo(
    () =>
      ({
        id: "grid__entitlements-list",
        columns,
        fields,
        views,
        isDefaultView: false,
        selectedView: "active",
        ...asyncOptions,
        onEvent: onGridActionEvent,
      }) as UseAsyncGridConfig<Entitlement>,
    [columns, fields, asyncOptions, onGridActionEvent],
  );

  const gridProps = useGridAsync(config);
  return { silentRefresh: asyncOptions.silentRefresh, refresh: asyncOptions.refresh, ...gridProps };
}
