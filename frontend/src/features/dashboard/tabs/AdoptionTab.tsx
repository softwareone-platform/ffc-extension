import { PATHS as ENTITLEMENT_PATHS } from "~features/entitlements/paths";
import { PATHS as ORGANIZATION_PATHS } from "~features/organizations/paths";
import { ChartLegend, DonutChart, PROVIDER_COLORS, XyChart } from "~shared/components/charts";
import { KpiTile } from "~shared/components/panel";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useAdoptionMetricsApi } from "../api";
import {
  CHART_HEIGHT,
  DATASOURCE_PROVIDER_SERIES,
  FUNNEL_SERIES,
  STATUS_DONUT_COLORS,
  STATUS_LEGEND_KEYS,
  TRIAL_VS_PAID_DONUT_COLORS,
  TRIAL_VS_PAID_TREND_SERIES,
} from "../chartConfig";
import { useDashboardFilters, withDashboardFilters } from "../components/DashboardFiltersContext";
import { MetricPanel } from "../components/MetricPanel";

const formatCount = (n: number) => n.toLocaleString("en-US");

export function AdoptionTab() {
  const tAdoption = useFixedT("dashboard:adoption");
  const { data } = useAdoptionMetricsApi();
  const { filters } = useDashboardFilters();

  if (!data) {
    return null;
  }

  const link = (path: string) => withDashboardFilters(path, filters);

  const statusLegendItems = STATUS_LEGEND_KEYS.map((key, index) => ({
    name: tAdoption(`overview:${key}`),
    color: STATUS_DONUT_COLORS[index],
  }));

  return (
    <div className={"ffc-tab-stack"}>
      <div className={"ffc-kpi-row ffc-kpi-row--four"}>
        <KpiTile
          label={tAdoption("overview:total")}
          value={formatCount(data.organizationsOverview.total)}
          linkTo={link(ORGANIZATION_PATHS.root)}
        />
        <KpiTile
          label={tAdoption("overview:active")}
          value={formatCount(data.organizationsOverview.active)}
          trend={"up"}
          linkTo={link(`${ORGANIZATION_PATHS.root}?status=active`)}
        />
        <KpiTile
          label={tAdoption("overview:terminated")}
          value={formatCount(data.organizationsOverview.terminated)}
          linkTo={link(`${ORGANIZATION_PATHS.root}?status=terminated`)}
        />
        <KpiTile
          label={tAdoption("overview:deleted")}
          value={formatCount(data.organizationsOverview.deleted)}
          trend={"down"}
          linkTo={link(`${ORGANIZATION_PATHS.root}?status=deleted`)}
        />
      </div>

      <div className={"ffc-panel-grid"}>
        <MetricPanel title={tAdoption("statusBreakdown:title")} className={"ffc-panel--span-4"}>
          <DonutChart
            data={data.organizationsOverview.statusDistribution}
            colors={STATUS_DONUT_COLORS}
            height={CHART_HEIGHT.lg}
          />
          <ChartLegend items={statusLegendItems} layout={"horizontal"} />
        </MetricPanel>

        <MetricPanel
          title={tAdoption("datasources:title")}
          className={"ffc-panel--span-8"}
          kpis={[
            {
              label: tAdoption("datasources:datasourceCount"),
              value: formatCount(data.datasources.datasourceCount),
            },
            {
              label: tAdoption("datasources:orgsWithDatasources"),
              value: formatCount(data.datasources.orgsWithDatasources),
            },
            {
              label: tAdoption("datasources:orgsWithoutDatasources"),
              value: formatCount(data.datasources.orgsWithoutDatasources),
              trend: "down",
            },
          ]}
          trend={
            <>
              <XyChart
                data={data.datasources.byProvider}
                categoryField={"period"}
                series={DATASOURCE_PROVIDER_SERIES}
                height={CHART_HEIGHT.sm}
                stacked
              />
              <ChartLegend items={DATASOURCE_PROVIDER_SERIES} layout={"horizontal"} />
            </>
          }
          asideLabel={tAdoption("datasources:providerDistribution")}
          aside={
            <DonutChart data={data.datasources.providerDistribution} colors={PROVIDER_COLORS} />
          }
        />

        <MetricPanel
          title={tAdoption("trialVsPaid:title")}
          kpis={[
            {
              label: tAdoption("trialVsPaid:paid"),
              value: formatCount(data.trialVsPaid.paid),
              linkTo: link(`${ENTITLEMENT_PATHS.root}?billing=paid`),
            },
            {
              label: tAdoption("trialVsPaid:trial"),
              value: formatCount(data.trialVsPaid.trial),
              linkTo: link(`${ENTITLEMENT_PATHS.root}?billing=trial`),
            },
          ]}
          trend={
            <>
              <XyChart
                data={data.trialVsPaid.monthlyTrend}
                categoryField={"month"}
                series={TRIAL_VS_PAID_TREND_SERIES}
                height={CHART_HEIGHT.xs}
              />
              <ChartLegend items={TRIAL_VS_PAID_TREND_SERIES} layout={"horizontal"} />
            </>
          }
          asideLabel={tAdoption("trialVsPaid:distribution")}
          aside={
            <DonutChart data={data.trialVsPaid.distribution} colors={TRIAL_VS_PAID_DONUT_COLORS} />
          }
        />

        <MetricPanel
          title={tAdoption("funnel:title")}
          description={tAdoption("funnel:description")}
        >
          <XyChart
            data={data.adoptionFunnel}
            categoryField={"month"}
            series={FUNNEL_SERIES}
            height={CHART_HEIGHT.lg}
          />
          <ChartLegend items={FUNNEL_SERIES} layout={"horizontal"} />
        </MetricPanel>
      </div>
    </div>
  );
}
