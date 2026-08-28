import {
  CHART_COLORS,
  ChartLegend,
  DonutChart,
  PROVIDER_COLORS,
  XyChart,
  XySeriesDef,
} from "~shared/components/charts";
import { KpiTile, Panel } from "~shared/components/panel";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useConsumptionMetricsApi } from "../api";

// Module scope keeps these referentially stable — the chart wrappers rebuild their
// amCharts root whenever `series`/`colors` change identity.
const SPEND_TREND_SERIES: XySeriesDef[] = [
  { field: "spend", name: "Spend", color: CHART_COLORS.blue, kind: "line" },
];

const USAGE_COVERAGE_SERIES: XySeriesDef[] = [
  { field: "coverage", name: "Coverage", color: CHART_COLORS.blueLight, kind: "area" },
];

const PROVIDER_TREND_SERIES: XySeriesDef[] = [
  { field: "azure", name: "Azure spend", color: CHART_COLORS.blue, kind: "area" },
  { field: "aws", name: "AWS spend", color: CHART_COLORS.orange, kind: "area" },
  { field: "gcp", name: "GCP spend", color: CHART_COLORS.green, kind: "area" },
];

const TOP_ORGANIZATIONS_SERIES: XySeriesDef[] = [
  { field: "spend", name: "Monthly spend", color: CHART_COLORS.blue, kind: "column" },
];

const COVERAGE_DONUT_COLORS = [CHART_COLORS.blue, CHART_COLORS.gray];
const USAGE_DONUT_COLORS = [CHART_COLORS.navy, CHART_COLORS.gray];

export function ConsumptionTab() {
  const tConsumption = useFixedT("dashboard:consumption");
  const { data } = useConsumptionMetricsApi();

  if (!data) {
    return null;
  }

  return (
    <div className={"ffc-panel-grid"}>
      <Panel title={tConsumption("monthlySpend:title")}>
        <div className={"ffc-kpi-row"}>
          <KpiTile
            label={tConsumption("monthlySpend:currentMonth")}
            value={data.monthlySpend.currentMonth}
          />
          <KpiTile
            label={tConsumption("monthlySpend:previousMonth")}
            value={data.monthlySpend.previousMonth}
          />
          <KpiTile
            label={tConsumption("monthlySpend:change")}
            value={data.monthlySpend.monthOverMonthChange}
            caption={tConsumption("monthlySpend:changeCaption")}
            trend={"down"}
          />
        </div>
      </Panel>

      <Panel title={tConsumption("coverage:title")}>
        <div className={"ffc-kpi-row"}>
          <KpiTile
            label={tConsumption("coverage:consumption")}
            value={data.coverage.consumption}
            caption={tConsumption("coverage:consumptionCaption")}
          />
          <KpiTile
            label={tConsumption("coverage:coverage")}
            value={data.coverage.coverage}
            caption={tConsumption("coverage:coverageCaption")}
          />
          <KpiTile
            label={tConsumption("coverage:usage")}
            value={data.coverage.usage}
            caption={tConsumption("coverage:usageCaption")}
          />
        </div>
      </Panel>

      <Panel title={tConsumption("spendTrend:title")}>
        <div className={"ffc-chart-split"}>
          <XyChart data={data.spendTrend} categoryField={"month"} series={SPEND_TREND_SERIES} />
          <div className={"ffc-chart-split__aside"}>
            <span className={"ffc-chart-split__aside-label"}>
              {tConsumption("spendTrend:distribution")}
            </span>
            <DonutChart data={data.coverageDistribution} colors={COVERAGE_DONUT_COLORS} />
          </div>
        </div>
      </Panel>

      <Panel title={tConsumption("usageCoverage:title")}>
        <div className={"ffc-chart-split"}>
          <XyChart
            data={data.usageCoverageTrend}
            categoryField={"month"}
            series={USAGE_COVERAGE_SERIES}
          />
          <div className={"ffc-chart-split__aside"}>
            <span className={"ffc-chart-split__aside-label"}>
              {tConsumption("usageCoverage:distribution")}
            </span>
            <DonutChart data={data.usageDistribution} colors={USAGE_DONUT_COLORS} />
          </div>
        </div>
      </Panel>

      <Panel title={tConsumption("providerDistribution:title")}>
        <div className={"ffc-chart-split"}>
          <DonutChart data={data.providerDistribution} colors={PROVIDER_COLORS} height={220} />
          <div>
            <XyChart
              data={data.providerTrend}
              categoryField={"month"}
              series={PROVIDER_TREND_SERIES}
              height={190}
              stacked
            />
            <ChartLegend items={PROVIDER_TREND_SERIES} layout={"horizontal"} />
          </div>
        </div>
      </Panel>

      <Panel title={tConsumption("topOrganizations:title")}>
        <XyChart
          data={data.topOrganizations}
          categoryField={"organization"}
          series={TOP_ORGANIZATIONS_SERIES}
          height={260}
          horizontal
        />
      </Panel>
    </div>
  );
}
