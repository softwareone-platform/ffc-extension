import { useMemo } from "react";

import { Chip } from "@swo/design-system/chip";
import {
  Grid,
  GridCellSimple,
  GridColumnDefinition,
  useGridInMemory,
} from "@swo/design-system/grid";

import { useFixedT } from "~shared/hooks/useFixedT";

import { MaturityRow } from "../api/model";
import { MATURITY_LEVELS } from "../maturityLevels";

const LEVEL_CHIP_COLORS = ["gray", "primary", "warning", "warning", "success"] as const;

export function MaturityGrid({ rows }: { rows: MaturityRow[] }) {
  const tColumns = useFixedT("dashboard:maturity:columns");
  const tLevels = useFixedT("dashboard:maturity:levels");
  const tFlags = useFixedT("dashboard:maturity:flags");

  const columns = useMemo((): GridColumnDefinition<MaturityRow>[] => {
    function flagCell(value: boolean) {
      return (
        <GridCellSimple>
          <Chip
            label={value ? tFlags("yes") : tFlags("no")}
            color={value ? "success" : "gray"}
            type={"outline"}
          />
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
        cell: (item) => <GridCellSimple>{item.lastActivity}</GridCellSimple>,
      },
    ];
  }, [tColumns, tLevels, tFlags]);

  const gridProps = useGridInMemory<MaturityRow>(rows, {
    id: "grid__dashboard-organization-maturity",
    columns,
  });

  return <Grid<MaturityRow> {...gridProps} />;
}
