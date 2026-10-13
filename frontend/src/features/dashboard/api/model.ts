/**
 * Dashboard domain enumerations. The `*_STATUSES`/`*_PROVIDERS` tuples back both the type
 * unions and the runtime option lists rendered in the filter sidebar.
 */
export const ORGANISATION_STATUSES = ["active", "paid", "trial", "terminated", "deleted"] as const;
export const CLOUD_PROVIDERS = ["azure", "aws", "gcp"] as const;

export type OrganisationStatus = (typeof ORGANISATION_STATUSES)[number];
export type CloudProvider = (typeof CLOUD_PROVIDERS)[number];

/** A row of chart data: one category field plus one numeric field per series. */
export type MetricPoint = Record<string, string | number>;

export type DistributionSlice = {
  category: string;
  value: number;
};

export type ConsumptionMetrics = {
  monthlySpend: {
    currentMonth: string;
    previousMonth: string;
    monthOverMonthChange: string;
  };
  coverage: {
    consumption: string;
    coverage: string;
    usage: string;
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
    total: string;
    active: string;
    terminated: string;
    deleted: string;
    statusDistribution: DistributionSlice[];
  };
  datasources: {
    total: string;
    withDatasources: string;
    withoutDatasources: string;
    providerDistribution: DistributionSlice[];
    byProvider: MetricPoint[];
  };
  adoptionFunnel: MetricPoint[];
  trialVsPaid: {
    trial: string;
    paid: string;
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
  lastActivity: string;
};

export type MaturityMetrics = {
  distribution: DistributionSlice[];
  byLevel: MetricPoint[];
  progression: MetricPoint[];
  rows: MaturityRow[];
};
