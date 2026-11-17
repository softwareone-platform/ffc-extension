import { useMemo } from "react";

import { GridCellDateTime, GridCellSimple, GridColumnDefinition } from "@swo/design-system/grid";
import { Paths } from "@swo/rql-client";

import { OrganizationEventRead } from "~api/ffc-api-model";
import { Status } from "~shared/components/entity-status-chip";
import { useFixedT } from "~shared/hooks/useFixedT";

type Columns = Array<
  Omit<GridColumnDefinition<OrganizationEventRead>, "fields"> & {
    fields: Paths<OrganizationEventRead>[];
  }
>;

export function useColumns(): Columns {
  const tColumns = useFixedT("shared:grid:columns");
  const tEvtClass = useFixedT("shared:grid:evt_class");

  return useMemo(() => {
    return [
      {
        name: "time",
        title: tColumns("time"),
        fields: ["time"],
        cell: (item: OrganizationEventRead) => <GridCellDateTime date={item.time} />,
        initialWidth: 200,
      },
      {
        name: "level",
        title: tColumns("level"),
        fields: ["level"],
        cell: (item: OrganizationEventRead) => (
          <GridCellSimple>
            <Status status={item.level.toLocaleLowerCase()}></Status>
          </GridCellSimple>
        ),

        initialWidth: 150,
      },
      {
        name: "description",
        title: tColumns("description"),
        fields: ["description"],
        cell: (item: OrganizationEventRead) => <GridCellSimple>{item.description}</GridCellSimple>,
      },
      {
        name: "evt_class",
        title: tColumns("evt_class"),
        fields: ["evt_class"],
        cell: (item: OrganizationEventRead) => (
          <GridCellSimple>{tEvtClass(item.evt_class.toLowerCase())}</GridCellSimple>
        ),
        isHidden: true,
        initialWidth: 250,
      },
      {
        name: "object_id",
        title: tColumns("object_id"),
        fields: ["object_id"],
        cell: (item: OrganizationEventRead) => <GridCellSimple>{item.object_id}</GridCellSimple>,
        isHidden: true,
      },
      {
        name: "object_name",
        title: tColumns("object_name"),
        fields: ["object_name"],
        cell: (item: OrganizationEventRead) => <GridCellSimple>{item.object_name}</GridCellSimple>,
        isHidden: true,
      },
    ];
  }, [tColumns, tEvtClass]);
}
