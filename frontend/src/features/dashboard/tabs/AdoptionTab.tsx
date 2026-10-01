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

import { PATHS as ENTITLEMENT_PATHS } from "~features/entitlements/paths";
import { PATHS as ORGANIZATION_PATHS } from "~features/organizations/paths";

import { useAdoptionMetricsApi } from "../api";
import { OrganizationsWithoutDatasourcesGrid } from "./OrganizationsWithoutDatasourcesGrid";

// Module scope keeps these referentially stable — the chart wrappers rebuild their
// amCharts root whenever `series`/`colors` change identity.
const STATUS_LEGEND_KEYS = ["active", "terminated", "deleted"] as const;
const STATUS_DONUT_COLORS = [CHART_COLORS.green, CHART_COLORS.orange, CHART_COLORS.gray];

const DATASOURCE_PROVIDER_SERIES: XySeriesDef[] = [
  { field: "azure", name: "Azure", color: CHART_COLORS.blue, kind: "column" },
  { field: "aws", name: "AWS", color: CHART_COLORS.orange, kind: "column" },
  { field: "gcp", name: "GCP", color: CHART_COLORS.green, kind: "column" },
];

// Horizontal column stands in for a dedicated funnel: stages descend top-to-bottom and the
// relative bar length communicates drop-off at each step without an extra chart primitive.
const FUNNEL_SERIES: XySeriesDef[] = [
  { field: "count", name: "Organizations", color: CHART_COLORS.blue, kind: "column" },
];

const TRIAL_VS_PAID_DONUT_COLORS = [CHART_COLORS.green, CHART_COLORS.yellow];

const TRIAL_VS_PAID_TREND_SERIES: XySeriesDef[] = [
  { field: "paid", name: "Paid", color: CHART_COLORS.green, kind: "line" },
  { field: "trial", name: "Trial", color: CHART_COLORS.yellow, kind: "line" },
];

export function AdoptionTab() {
  const tAdoption = useFixedT("dashboard:adoption");
  const { data } = useAdoptionMetricsApi();

  if (!data) {
    return null;
  }

  const statusLegendItems = STATUS_LEGEND_KEYS.map((key, index) => ({
    name: tAdoption(`overview:${key}`),
    color: STATUS_DONUT_COLORS[index],
  }));

  return (
    <div className={"ffc-tab-stack"}>
      <div className={"ffc-kpi-row ffc-kpi-row--four"}>
        <KpiTile
          label={tAdoption("overview:total")}
          value={data.organizationsOverview.total}
          linkTo={ORGANIZATION_PATHS.root}
        />
        <KpiTile
          label={tAdoption("overview:active")}
          value={data.organizationsOverview.active}
          trend={"up"}
          linkTo={`${ORGANIZATION_PATHS.root}?status=active`}
        />
        <KpiTile
          label={tAdoption("overview:terminated")}
          value={data.organizationsOverview.terminated}
          linkTo={`${ORGANIZATION_PATHS.root}?status=terminated`}
        />
        <KpiTile
          label={tAdoption("overview:deleted")}
          value={data.organizationsOverview.deleted}
          trend={"down"}
          linkTo={`${ORGANIZATION_PATHS.root}?status=deleted`}
        />
      </div>

      <div className={"ffc-panel-grid"}>
        <Panel title={tAdoption("statusBreakdown:title")} className={"ffc-panel--span-4"}>
          <DonutChart
            data={data.organizationsOverview.statusDistribution}
            colors={STATUS_DONUT_COLORS}
            height={260}
          />
          <ChartLegend items={statusLegendItems} layout={"horizontal"} />
        </Panel>

      <Panel title={tAdoption("datasources:title")} className={"ffc-panel--span-8"}>
        <div className={"ffc-kpi-row"}>
          <KpiTile label={tAdoption("datasources:total")} value={data.datasources.total} />
          <KpiTile
            label={tAdoption("datasources:withDatasources")}
            value={data.datasources.withDatasources}
          />
          <KpiTile
            label={tAdoption("datasources:withoutDatasources")}
            value={data.datasources.withoutDatasources}
            trend={"down"}
          />
        </div>
        <div className={"ffc-chart-split"}>
          <div>
            <XyChart
              data={data.datasources.byProvider}
              categoryField={"period"}
              series={DATASOURCE_PROVIDER_SERIES}
              height={200}
              stacked
            />
            <ChartLegend items={DATASOURCE_PROVIDER_SERIES} layout={"horizontal"} />
          </div>
          <div className={"ffc-chart-split__aside"}>
            <span className={"ffc-chart-split__aside-label"}>
              {tAdoption("datasources:providerDistribution")}
            </span>
            <DonutChart data={data.datasources.providerDistribution} colors={PROVIDER_COLORS} />
          </div>
        </div>
      </Panel>

      <Panel title={tAdoption("trialVsPaid:title")}>
        <div className={"ffc-kpi-row"}>
          <KpiTile
            label={tAdoption("trialVsPaid:paid")}
            value={data.trialVsPaid.paid}
            linkTo={`${ENTITLEMENT_PATHS.root}?billing=paid`}
          />
          <KpiTile
            label={tAdoption("trialVsPaid:trial")}
            value={data.trialVsPaid.trial}
            linkTo={`${ENTITLEMENT_PATHS.root}?billing=trial`}
          />
        </div>
        <div className={"ffc-chart-split"}>
          <div>
            <XyChart
              data={data.trialVsPaid.monthlyTrend}
              categoryField={"month"}
              series={TRIAL_VS_PAID_TREND_SERIES}
              height={190}
            />
            <ChartLegend items={TRIAL_VS_PAID_TREND_SERIES} layout={"horizontal"} />
          </div>
          <div className={"ffc-chart-split__aside"}>
            <span className={"ffc-chart-split__aside-label"}>
              {tAdoption("trialVsPaid:distribution")}
            </span>
            <DonutChart data={data.trialVsPaid.distribution} colors={TRIAL_VS_PAID_DONUT_COLORS} />
          </div>
        </div>
      </Panel>

      <Panel title={tAdoption("funnel:title")}>
        <p className={"ffc-panel__description"}>{tAdoption("funnel:description")}</p>
        <XyChart
          data={data.adoptionFunnel}
          categoryField={"stage"}
          series={FUNNEL_SERIES}
          height={260}
          horizontal
        />
      </Panel>

      <Panel title={tAdoption("withoutDatasources:title")} className={"ffc-panel--full"}>
        <p className={"ffc-panel__description"}>{tAdoption("withoutDatasources:description")}</p>
        <OrganizationsWithoutDatasourcesGrid rows={data.organizationsWithoutDatasources} />
      </Panel>
      </div>
    </div>
  );
}
