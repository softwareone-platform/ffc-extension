import { useMemo } from "react";

import { differenceInCalendarDays, parseISO } from "date-fns";

import { Chip } from "@swo/design-system/chip";
import {
  Grid,
  GridCellSimple,
  GridColumnDefinition,
  GridFieldDefinition,
  GridFieldSortOperation,
  useGridInMemory,
} from "@swo/design-system/grid";
import { useFormatDate } from "@swo/design-system/utils";

import { useFixedT } from "~shared/hooks/useFixedT";

import { OrganizationWithoutDatasources } from "../api/model";

type Priority = "high" | "medium" | "low";

type Row = OrganizationWithoutDatasources & { daysSinceCreation: number; priority: Priority };

const PRIORITY_CHIP_COLORS = { high: "danger", medium: "warning", low: "gray" } as const;
const BILLING_CHIP_COLORS = { paid: "success", trial: "warning" } as const;

// Longest without a datasource first — the rows most in need of a follow-up.
const INITIAL_SORT: GridFieldSortOperation[] = [{ field: "daysSinceCreation", direction: "desc" }];

// Three weeks without a datasource means onboarding has stalled; under a week is still normal.
function priorityFor(days: number): Priority {
  if (days >= 21) return "high";
  if (days >= 7) return "medium";
  return "low";
}

export function NoDatasourcesGrid({ rows }: { rows: OrganizationWithoutDatasources[] }) {
  const tColumns = useFixedT("dashboard:adoption:noDatasources:columns");
  const tPriority = useFixedT("dashboard:adoption:noDatasources:priority");
  const tBilling = useFixedT("dashboard:filters:billing");
  const tDays = useFixedT("dashboard:adoption:noDatasources");
  const formatDate = useFormatDate();

  // Days are counted from today rather than stored, so the mock never goes stale.
  const gridRows = useMemo((): Row[] => {
    const today = new Date();
    return rows.map((row) => {
      const daysSinceCreation = differenceInCalendarDays(today, parseISO(row.createdAt));
      return { ...row, daysSinceCreation, priority: priorityFor(daysSinceCreation) };
    });
  }, [rows]);

  const columns = useMemo(
    (): GridColumnDefinition<Row>[] => [
      {
        name: "priority",
        title: tColumns("priority"),
        initialWidth: 110,
        cell: (item) => (
          <GridCellSimple>
            <Chip label={tPriority(item.priority)} color={PRIORITY_CHIP_COLORS[item.priority]} />
          </GridCellSimple>
        ),
      },
      {
        name: "organizationName",
        title: tColumns("organizationName"),
        initialWidth: 180,
        cell: (item) => <GridCellSimple>{item.organizationName}</GridCellSimple>,
      },
      {
        name: "createdAt",
        title: tColumns("createdAt"),
        initialWidth: 125,
        cell: (item) => <GridCellSimple>{formatDate(item.createdAt)}</GridCellSimple>,
      },
      {
        name: "billingStatus",
        title: tColumns("billingStatus"),
        initialWidth: 130,
        cell: (item) => (
          <GridCellSimple>
            <Chip
              label={tBilling(item.billingStatus)}
              color={BILLING_CHIP_COLORS[item.billingStatus]}
            />
          </GridCellSimple>
        ),
      },
      {
        name: "daysSinceCreation",
        title: tColumns("daysSinceCreation"),
        initialWidth: 140,
        cell: (item) => (
          <GridCellSimple>{tDays("days", { count: item.daysSinceCreation })}</GridCellSimple>
        ),
      },
    ],
    [tColumns, tPriority, tBilling, tDays, formatDate],
  );

  const fields = useMemo(
    (): GridFieldDefinition[] => [
      {
        name: "priority",
        title: tColumns("priority"),
        type: "list",
        options: (["high", "medium", "low"] as const).map((value) => ({
          value,
          label: tPriority(value),
        })),
      },
      { name: "organizationName", title: tColumns("organizationName"), type: "text" },
      { name: "createdAt", title: tColumns("createdAt"), type: "date" },
      {
        name: "billingStatus",
        title: tColumns("billingStatus"),
        type: "list",
        options: (["trial", "paid"] as const).map((value) => ({ value, label: tBilling(value) })),
      },
      { name: "daysSinceCreation", title: tColumns("daysSinceCreation"), type: "number" },
    ],
    [tColumns, tPriority, tBilling],
  );

  const gridProps = useGridInMemory<Row>(gridRows, {
    id: "grid__dashboard-organizations-without-datasources",
    columns,
    fields,
    sort: INITIAL_SORT,
  });

  return <Grid<Row> {...gridProps} />;
}
