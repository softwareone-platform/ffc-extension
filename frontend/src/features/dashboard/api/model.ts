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
