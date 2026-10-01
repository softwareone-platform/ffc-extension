import { useMemo } from "react";

import { Chip } from "@swo/design-system/chip";
import {
  Grid,
  GridCellSimple,
  GridColumnDefinition,
  GridFieldDefinition,
  GridFieldSortOperation,
  useGridInMemory,
} from "@swo/design-system/grid";

import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatDate } from "~shared/hooks/useFormatDate";

import { OrganizationWithoutDatasourceRow } from "../api/model";

// Threshold above which "days since creation" is flagged as a stalled onboarding — matches
// the Customer Success definition of a lapsed trial / unfinished setup.
const STALE_ONBOARDING_DAYS = 30;

// Default sort applied by the in-memory grid: newest creations first, matching the "Descending
// by Creation Date" requirement from the BDR.
const INITIAL_SORT: GridFieldSortOperation[] = [{ field: "creationDate", direction: "desc" }];

export function OrganizationsWithoutDatasourcesGrid({
  rows,
}: {
  rows: OrganizationWithoutDatasourceRow[];
}) {
  const tColumns = useFixedT("dashboard:adoption:withoutDatasources:columns");
  const tStatus = useFixedT("dashboard:adoption:withoutDatasources:status");
  const formatDate = useFormatDate();

  const columns = useMemo((): GridColumnDefinition<OrganizationWithoutDatasourceRow>[] => {
    return [
      {
        name: "organizationName",
        title: tColumns("organizationName"),
        cell: (item) => <GridCellSimple>{item.organizationName}</GridCellSimple>,
      },
      {
        name: "creationDate",
        title: tColumns("creationDate"),
        cell: (item) => <GridCellSimple>{formatDate(item.creationDate)}</GridCellSimple>,
      },
      {
        name: "status",
        title: tColumns("status"),
        cell: (item) => (
          <GridCellSimple>
            <Chip
              label={tStatus(item.status)}
              color={item.status === "paid" ? "success" : "primary"}
              type={"outline"}
            />
          </GridCellSimple>
        ),
      },
      {
        name: "daysSinceCreation",
        title: tColumns("daysSinceCreation"),
        cell: (item) => (
          <GridCellSimple>
            <Chip
              label={String(item.daysSinceCreation)}
              color={item.daysSinceCreation >= STALE_ONBOARDING_DAYS ? "warning" : "gray"}
            />
          </GridCellSimple>
        ),
      },
    ];
  }, [tColumns, tStatus, formatDate]);

  // Field definitions back the grid's sort/filter machinery — the in-memory grid compares the
  // raw row value for the named field, so `creationDate` is kept as ISO (YYYY-MM-DD) in the
  // mock and formatted for display inside the cell above.
  const fields = useMemo(
    (): GridFieldDefinition[] => [
      { name: "organizationName", title: tColumns("organizationName"), type: "text" },
      { name: "creationDate", title: tColumns("creationDate"), type: "date" },
      { name: "status", title: tColumns("status"), type: "text" },
      { name: "daysSinceCreation", title: tColumns("daysSinceCreation"), type: "number" },
    ],
    [tColumns],
  );

  const gridProps = useGridInMemory<OrganizationWithoutDatasourceRow>(rows, {
    id: "grid__dashboard-organizations-without-datasources",
    columns,
    fields,
    sort: INITIAL_SORT,
  });

  return <Grid<OrganizationWithoutDatasourceRow> {...gridProps} />;
}
