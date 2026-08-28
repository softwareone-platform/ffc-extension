import { ChartLegend, DonutChart, XyChart } from "~shared/components/charts";
import { Panel } from "~shared/components/panel";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useMaturityMetricsApi } from "../api";
import {
  MATURITY_AREA_SERIES,
  MATURITY_COLORS,
  MATURITY_COLUMN_SERIES,
  MATURITY_LEVELS,
} from "../maturityLevels";
import { MaturityGrid } from "./MaturityGrid";

export function MaturityTab() {
  const tMaturity = useFixedT("dashboard:maturity");
  const tLevels = useFixedT("dashboard:maturity:levels");
  const { data } = useMaturityMetricsApi();

  if (!data) {
    return null;
  }

  const legendItems = MATURITY_LEVELS.map((entry) => ({
    name: `${entry.level}: ${tLevels(entry.key)}`,
    color: entry.color,
  }));

  return (
    <div className={"ffc-panel-grid"}>
      <Panel title={tMaturity("dashboard:title")}>
        <div className={"ffc-chart-split ffc-chart-split--triple"}>
          <ChartLegend heading={tMaturity("dashboard:level")} items={legendItems} />
          <DonutChart data={data.distribution} colors={MATURITY_COLORS} height={190} />
          <XyChart
            data={data.byLevel}
            categoryField={"bucket"}
            series={MATURITY_COLUMN_SERIES}
            height={190}
            stacked
          />
        </div>
      </Panel>

      <Panel title={tMaturity("progression:title")}>
        <XyChart
          data={data.progression}
          categoryField={"month"}
          series={MATURITY_AREA_SERIES}
          height={200}
          stacked
        />
        <ChartLegend layout={"horizontal"} items={legendItems} />
      </Panel>

      <Panel title={tMaturity("table:title")} className={"ffc-panel--full"}>
        <MaturityGrid rows={data.rows} />
      </Panel>
    </div>
  );
}
