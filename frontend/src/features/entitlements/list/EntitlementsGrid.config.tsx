import { useMemo } from "react";

import { Link } from "react-router-dom";

import { EntityReference } from "@swo/design-system/entity-reference";
import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import {
  GridCellSimple,
  GridCellTitleSubtitle,
  GridColumnDefinition,
  GridFieldDefinition,
  GridInMemoryConfig,
  useGridInMemory,
} from "@swo/design-system/grid";
import { getStatusLabel } from "@swo/mp-status-chip";
import { Paths } from "@swo/rql-client";

import CustomIcon from "~shared/components/custom-icons/CustomIcon";
import { Status } from "~shared/components/entity-status-chip/EntityStatusChip";
import { useFixedT } from "~shared/hooks/useFixedT";

import { mockEntitlements } from "../api/mockData";
import { Entitlement } from "../api/model";

// Sandbox: client-side grid over static entitlements.
type Columns = Array<
  Omit<GridColumnDefinition<Entitlement>, "fields"> & { fields: Paths<Entitlement>[] }
>;

const noop = () => {};

export function useGridConfig() {
  const tColumns = useFixedT("shared:grid:columns");
  const tFields = useFixedT("shared:grid:fields");

  const config = useMemo(() => {
    const columns: Columns = [
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
            <Status<Entitlement> item={item} />
          </GridCellSimple>
        ),
        initialWidth: 100,
      },
    ];

    const fields: GridFieldDefinition[] = [
      { title: tFields("entitlement:id"), name: "id" },
      { title: tFields("entitlement:name"), name: "name" },
      { title: tFields("affiliate:name"), name: "owner.name" },
      { title: tFields("affiliate:id"), name: "owner.id" },
      { title: tFields("affiliate_external_id"), name: "affiliate_external_id" },
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
    ];

    return {
      id: "grid__entitlements-list",
      columns,
      fields,
      isDefaultView: true,
      selectedView: "default",
    } as GridInMemoryConfig<Entitlement>;
  }, [tColumns, tFields]);

  return { refresh: noop, silentRefresh: noop, ...useGridInMemory(mockEntitlements, config) };
}
