import { useMemo } from "react";

import { Link } from "react-router-dom";

import {
  GridCellDateTime,
  GridCellSimple,
  GridCellTitleSubtitle,
  GridColumnDefinition,
} from "@swo/design-system/grid";
import { DisplayValue } from "@swo/design-system/utils";
import { Paths } from "@swo/rql-client";

import { OrganizationRead } from "~api/ffc-api-model";
import { Status } from "~shared/components/entity-status-chip/EntityStatusChip";
import { GridCellDynamicActions } from "~shared/components/grid/GridCellDynamicActions";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useUserRole } from "~shared/hooks/useUserRole";

import { useActionOptions } from "./useActionOptions";

type Columns = Array<
  Omit<GridColumnDefinition<OrganizationRead>, "fields"> & {
    fields: Paths<OrganizationRead>[];
  }
>;

export function useColumns(): Columns {
  const tColumns = useFixedT("shared:grid:columns");
  const getActions = useActionOptions();
  const { role } = useUserRole();

  return useMemo(() => {
    return [
      {
        name: "name",
        title: tColumns("organization"),
        fields: ["name", "id", "linked_organization_id"],
        cell: (item: OrganizationRead) => (
          <GridCellTitleSubtitle
            title={<Link to={`${item.id}/general`}>{item.name}</Link>}
            subtitle={`${item.id} | ${item.linked_organization_id}`}
          />
        ),
      },
      {
        name: "currency",
        title: tColumns("currency"),
        fields: ["currency"],
        cell: (item: OrganizationRead) => <GridCellSimple>{item.currency}</GridCellSimple>,
        initialWidth: 175,
      },
      {
        name: "billing_currency",
        title: tColumns("billing_currency"),
        fields: ["billing_currency"],
        cell: (item: OrganizationRead) => (
          <GridCellSimple>
            <DisplayValue value={item.billing_currency} />
          </GridCellSimple>
        ),
        initialWidth: 175,
      },
      {
        name: "operations_additional_id",
        title: tColumns("operations_additional_id"),
        fields: ["operations_external_id"],
        cell: (item: OrganizationRead) => (
          <GridCellSimple>{item.operations_external_id}</GridCellSimple>
        ),
        initialWidth: 350,
      },
      {
        name: "created_at",
        title: tColumns("created_at"),
        fields: ["events.created.at"],
        cell: (item: OrganizationRead) => <GridCellDateTime date={item.events?.created?.at} />,
        initialWidth: 150,
        isHidden: true,
      },
      {
        name: "updated_at",
        title: tColumns("updated_at"),
        fields: ["events.updated.at"],
        cell: (item: OrganizationRead) => <GridCellDateTime date={item.events?.updated?.at} />,
        initialWidth: 150,
        isHidden: true,
      },
      {
        name: "terminated_at",
        title: tColumns("terminated_at"),
        fields: ["events.terminated.at"],
        cell: (item: OrganizationRead) => <GridCellDateTime date={item.events?.terminated?.at} />,
        initialWidth: 150,
        isHidden: true,
      },
      {
        name: "status",
        title: tColumns("status"),
        fields: ["status"],
        cell: (item: OrganizationRead) => (
          <GridCellSimple>
            <Status<OrganizationRead> item={item}></Status>
          </GridCellSimple>
        ),
        initialWidth: 150,
      },
      {
        name: "actions",
        title: tColumns("actions"),
        fields: [],
        cell: (item: OrganizationRead) => (
          <GridCellDynamicActions<OrganizationRead> item={item} actions={getActions(item)} />
        ),
        initialWidth: 100,
        isScalable: false,
        isHidden: role !== "admin",
      },
    ];
  }, [tColumns, getActions, role]);
}
