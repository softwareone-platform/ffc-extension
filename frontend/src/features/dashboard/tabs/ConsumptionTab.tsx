import { ChartLegend, DonutChart, PROVIDER_COLORS, XyChart } from "~shared/components/charts";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useConsumptionMetricsApi } from "../api";
import {
  CHART_HEIGHT,
  COVERAGE_DONUT_COLORS,
  PROVIDER_TREND_SERIES,
  SPEND_TREND_SERIES,
  TOP_ORGANIZATIONS_SERIES,
  USAGE_COVERAGE_SERIES,
  USAGE_DONUT_COLORS,
} from "../chartConfig";
import { MetricPanel } from "../components/MetricPanel";

const formatCurrency = (n: number) => `$${n.toLocaleString("en-US")}`;
const formatPercent = (n: number) => `${n}%`;
const formatSignedPercent = (n: number) =>
  `${n > 0 ? "+" : ""}${n.toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;

export function ConsumptionTab() {
  const tConsumption = useFixedT("dashboard:consumption");
  const { data } = useConsumptionMetricsApi();

  if (!data) {
    return null;
  }

  return (
    <div className={"ffc-panel-grid"}>
      <MetricPanel
        title={tConsumption("monthlySpend:title")}
        kpis={[
          {
            label: tConsumption("monthlySpend:currentMonth"),
            value: formatCurrency(data.monthlySpend.currentMonth),
          },
          {
            label: tConsumption("monthlySpend:previousMonth"),
            value: formatCurrency(data.monthlySpend.previousMonth),
          },
          {
            label: tConsumption("monthlySpend:change"),
            value: formatSignedPercent(data.monthlySpend.monthOverMonthChange),
            caption: tConsumption("monthlySpend:changeCaption"),
            trend: data.monthlySpend.monthOverMonthChange >= 0 ? "up" : "down",
          },
        ]}
      />

      <MetricPanel
        title={tConsumption("coverage:title")}
        kpis={[
          {
            label: tConsumption("coverage:consumptionCoverage"),
            value: formatPercent(data.coverage.consumptionCoverage),
            caption: tConsumption("coverage:consumptionCoverageCaption"),
          },
          {
            label: tConsumption("coverage:datasourceCoverage"),
            value: formatPercent(data.coverage.datasourceCoverage),
            caption: tConsumption("coverage:datasourceCoverageCaption"),
          },
          {
            label: tConsumption("coverage:usageCoverage"),
            value: formatPercent(data.coverage.usageCoverage),
            caption: tConsumption("coverage:usageCoverageCaption"),
          },
        ]}
      />

      <MetricPanel
        title={tConsumption("spendTrend:title")}
        trend={
          <XyChart data={data.spendTrend} categoryField={"month"} series={SPEND_TREND_SERIES} />
        }
        asideLabel={tConsumption("spendTrend:distribution")}
        aside={<DonutChart data={data.coverageDistribution} colors={COVERAGE_DONUT_COLORS} />}
      />

      <MetricPanel
        title={tConsumption("usageCoverage:title")}
        trend={
          <XyChart
            data={data.usageCoverageTrend}
            categoryField={"month"}
            series={USAGE_COVERAGE_SERIES}
          />
        }
        asideLabel={tConsumption("usageCoverage:distribution")}
        aside={<DonutChart data={data.usageDistribution} colors={USAGE_DONUT_COLORS} />}
      />

      <MetricPanel title={tConsumption("providerDistribution:title")}>
        <div className={"ffc-chart-split"}>
          <DonutChart
            data={data.providerDistribution}
            colors={PROVIDER_COLORS}
            height={CHART_HEIGHT.md}
          />
          <div>
            <XyChart
              data={data.providerTrend}
              categoryField={"month"}
              series={PROVIDER_TREND_SERIES}
              height={CHART_HEIGHT.xs}
              stacked
            />
            <ChartLegend items={PROVIDER_TREND_SERIES} layout={"horizontal"} />
          </div>
        </div>
      </MetricPanel>

      <MetricPanel title={tConsumption("topOrganizations:title")}>
        <XyChart
          data={data.topOrganizations}
          categoryField={"organization"}
          series={TOP_ORGANIZATIONS_SERIES}
          height={CHART_HEIGHT.lg}
          horizontal
        />
      </MetricPanel>
    </div>
  );
}
