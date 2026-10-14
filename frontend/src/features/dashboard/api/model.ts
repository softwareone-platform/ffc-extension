/**
 * Dashboard domain enumerations. The `*_STATUSES`/`*_PROVIDERS` tuples back both the type
 * unions and the runtime option lists rendered in the filter sidebar.
 */
export const ORGANISATION_STATUSES = ["active", "paid", "trial", "terminated", "deleted"] as const;
export const CLOUD_PROVIDERS = ["azure", "aws", "gcp"] as const;

export type OrganisationStatus = (typeof ORGANISATION_STATUSES)[number];
export type CloudProvider = (typeof CLOUD_PROVIDERS)[number];

/**
 * A row of chart data: one category field plus one numeric field per series. Monthly rows key
 * the category as `month`/`period` holding the ISO 8601 UTC month start (`2025-12-01T00:00:00Z`).
 */
export type MetricPoint = Record<string, string | number>;

export type DistributionSlice = {
  category: string;
  value: number;
};

export type ConsumptionMetrics = {
  monthlySpend: {
    /** Spend for the latest closed month, matching `spendTrend[length-1].spend`. */
    currentMonth: number;
    /** Spend for the month before `currentMonth`, matching `spendTrend[length-2].spend`. */
    previousMonth: number;
    /** Signed percent change from `previousMonth` to `currentMonth` (e.g. 5.44 or -1.2). */
    monthOverMonthChange: number;
  };
  coverage: {
    /** Share of organisations streaming consumption data (0-100). */
    consumptionCoverage: number;
    /** Share of organisations with at least one connected datasource (0-100). */
    datasourceCoverage: number;
    /** Share of organisations with active FinOps usage (0-100), matches `usageCoverageTrend` tail. */
    usageCoverage: number;
  };
  spendTrend: MetricPoint[];
  usageCoverageTrend: MetricPoint[];
  coverageDistribution: DistributionSlice[];
  usageDistribution: DistributionSlice[];
  providerDistribution: DistributionSlice[];
  providerTrend: MetricPoint[];
  topOrganizations: MetricPoint[];
};

export type AdoptionMetrics = {
  organizationsOverview: {
    total: number;
    active: number;
    terminated: number;
    deleted: number;
    statusDistribution: DistributionSlice[];
  };
  datasources: {
    /** Total datasource connections across all orgs (sum of `byProvider` tail row). */
    datasourceCount: number;
    /** Count of organisations with ≥1 datasource (matches `adoptionFunnel` tail `connected`). */
    orgsWithDatasources: number;
    /** Count of organisations with 0 datasources (`organizationsOverview.total − orgsWithDatasources`). */
    orgsWithoutDatasources: number;
    providerDistribution: DistributionSlice[];
    byProvider: MetricPoint[];
  };
  adoptionFunnel: MetricPoint[];
  trialVsPaid: {
    trial: number;
    paid: number;
    distribution: DistributionSlice[];
    monthlyTrend: MetricPoint[];
  };
};

export type MaturityRow = {
  id: string;
  organizationName: string;
  level: number;
  dataSources: number;
  hasConsumption: boolean;
  hasUsage: boolean;
  hasRecommendations: boolean;
  /** ISO 8601 UTC datetime (e.g. `2025-12-01T00:00:00Z`) — sorts chronologically as a string. */
  lastActivity: string;
};

export type MaturityMetrics = {
  /** Absolute org counts per maturity level — sum should match the latest total org population. */
  distribution: DistributionSlice[];
  byLevel: MetricPoint[];
  progression: MetricPoint[];
  rows: MaturityRow[];
};
