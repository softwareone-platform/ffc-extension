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

import { ORGANISATION_STATUSES, TopSpendOrganization } from "../api/model";

// Same green / gray / red reading as the status donut and the sidebar swatches.
const STATUS_CHIP_COLORS = { active: "success", terminated: "gray", deleted: "danger" } as const;

const INITIAL_SORT: GridFieldSortOperation[] = [{ field: "monthlySpend", direction: "desc" }];

const formatCurrency = (n: number) => `$${n.toLocaleString("en-US")}`;

export function TopSpendGrid({ rows }: { rows: TopSpendOrganization[] }) {
  const tColumns = useFixedT("dashboard:adoption:topSpend:columns");
  const tStatus = useFixedT("dashboard:filters:status");

  const columns = useMemo(
    (): GridColumnDefinition<TopSpendOrganization>[] => [
      {
        name: "organizationName",
        title: tColumns("organizationName"),
        initialWidth: 210,
        cell: (item) => <GridCellSimple>{item.organizationName}</GridCellSimple>,
      },
      {
        name: "status",
        title: tColumns("status"),
        initialWidth: 130,
        cell: (item) => (
          <GridCellSimple>
            <Chip label={tStatus(item.status)} color={STATUS_CHIP_COLORS[item.status]} />
          </GridCellSimple>
        ),
      },
      {
        name: "monthlySpend",
        title: tColumns("monthlySpend"),
        initialWidth: 120,
        cell: (item) => <GridCellSimple>{formatCurrency(item.monthlySpend)}</GridCellSimple>,
      },
    ],
    [tColumns, tStatus],
  );

  const fields = useMemo(
    (): GridFieldDefinition[] => [
      { name: "organizationName", title: tColumns("organizationName"), type: "text" },
      {
        name: "status",
        title: tColumns("status"),
        type: "list",
        options: ORGANISATION_STATUSES.map((value) => ({ value, label: tStatus(value) })),
      },
      { name: "monthlySpend", title: tColumns("monthlySpend"), type: "number" },
    ],
    [tColumns, tStatus],
  );

  const gridProps = useGridInMemory<TopSpendOrganization>(rows, {
    id: "grid__dashboard-top-organizations-by-spend",
    columns,
    fields,
    sort: INITIAL_SORT,
    // A fixed, pre-sorted list of ten: there is nothing to page through, and in a 5/12 panel
    // the toolbar would only wrap.
    isToHideToolbar: true,
    isToHideFooter: true,
  });

  return <Grid<TopSpendOrganization> {...gridProps} />;
}
