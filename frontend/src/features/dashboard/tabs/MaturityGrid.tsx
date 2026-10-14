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

import { GridCellDate } from "~shared/components/grid/GridCellDate";
import { useFixedT } from "~shared/hooks/useFixedT";

import { MaturityRow } from "../api/model";
import { MATURITY_LEVELS } from "../maturityLevels";

const LEVEL_CHIP_COLORS = ["gray", "primary", "warning", "warning", "success"] as const;

// Highest maturity first — matches the narrative of the maturity tab (celebrate operationalized tenants).
const INITIAL_SORT: GridFieldSortOperation[] = [{ field: "level", direction: "desc" }];

export function MaturityGrid({ rows }: { rows: MaturityRow[] }) {
  const tColumns = useFixedT("dashboard:maturity:columns");
  const tLevels = useFixedT("dashboard:maturity:levels");
  const tFlags = useFixedT("dashboard:maturity:flags");

  const columns = useMemo((): GridColumnDefinition<MaturityRow>[] => {
    function flagCell(value: boolean) {
      return (
        <GridCellSimple>
          <Chip label={value ? tFlags("yes") : tFlags("no")} color={value ? "success" : "gray"} />
        </GridCellSimple>
      );
    }

    return [
      {
        name: "organizationName",
        title: tColumns("organizationName"),
        cell: (item) => <GridCellSimple>{item.organizationName}</GridCellSimple>,
      },
      {
        name: "level",
        title: tColumns("level"),
        cell: (item) => (
          <GridCellSimple>
            <Chip
              label={tLevels(MATURITY_LEVELS[item.level].key)}
              color={LEVEL_CHIP_COLORS[item.level]}
            />
          </GridCellSimple>
        ),
      },
      {
        name: "dataSources",
        title: tColumns("dataSources"),
        cell: (item) => <GridCellSimple>{String(item.dataSources)}</GridCellSimple>,
      },
      {
        name: "hasConsumption",
        title: tColumns("consumptionStatus"),
        cell: (item) => flagCell(item.hasConsumption),
      },
      {
        name: "hasUsage",
        title: tColumns("usageStatus"),
        cell: (item) => flagCell(item.hasUsage),
      },
      {
        name: "hasRecommendations",
        title: tColumns("recommendationStatus"),
        cell: (item) => flagCell(item.hasRecommendations),
      },
      {
        name: "lastActivity",
        title: tColumns("lastActivity"),
        cell: (item) => <GridCellDate value={item.lastActivity} />,
      },
    ];
  }, [tColumns, tLevels, tFlags]);

  const fields = useMemo(
    (): GridFieldDefinition[] => [
      { name: "organizationName", title: tColumns("organizationName"), type: "text" },
      { name: "level", title: tColumns("level"), type: "number" },
      { name: "dataSources", title: tColumns("dataSources"), type: "number" },
      { name: "hasConsumption", title: tColumns("consumptionStatus"), type: "boolean" },
      { name: "hasUsage", title: tColumns("usageStatus"), type: "boolean" },
      { name: "hasRecommendations", title: tColumns("recommendationStatus"), type: "boolean" },
      { name: "lastActivity", title: tColumns("lastActivity"), type: "date" },
    ],
    [tColumns],
  );

  const gridProps = useGridInMemory<MaturityRow>(rows, {
    id: "grid__dashboard-organization-maturity",
    columns,
    fields,
    sort: INITIAL_SORT,
  });

  return <Grid<MaturityRow> {...gridProps} />;
}
