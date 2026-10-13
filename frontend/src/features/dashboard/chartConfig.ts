import { CHART_COLORS, XySeriesDef } from "~shared/components/charts";

/**
 * Canonical chart heights for the dashboard. The scale is intentionally small —
 * if a new value is needed, extend here rather than inlining a magic number.
 */
export const CHART_HEIGHT = { xs: 190, sm: 200, md: 220, lg: 260 } as const;

// === Adoption ===

export const STATUS_LEGEND_KEYS = ["active", "terminated", "deleted"] as const;
export const STATUS_DONUT_COLORS = [CHART_COLORS.green, CHART_COLORS.orange, CHART_COLORS.gray];

export const DATASOURCE_PROVIDER_SERIES: XySeriesDef[] = [
  { field: "azure", name: "Azure", color: CHART_COLORS.blue, kind: "column" },
  { field: "aws", name: "AWS", color: CHART_COLORS.navy, kind: "column" },
  { field: "gcp", name: "GCP", color: CHART_COLORS.yellow, kind: "column" },
];

export const FUNNEL_SERIES: XySeriesDef[] = [
  { field: "created", name: "Organization Created", color: CHART_COLORS.blue, kind: "line" },
  { field: "connected", name: "Datasource Connected", color: CHART_COLORS.green, kind: "line" },
  { field: "dataAvailable", name: "Data Available", color: CHART_COLORS.yellow, kind: "line" },
  { field: "active", name: "Active Platform Usage", color: CHART_COLORS.orange, kind: "line" },
];

export const TRIAL_VS_PAID_DONUT_COLORS = [CHART_COLORS.green, CHART_COLORS.yellow];

export const TRIAL_VS_PAID_TREND_SERIES: XySeriesDef[] = [
  { field: "paid", name: "Paid", color: CHART_COLORS.green, kind: "line" },
  { field: "trial", name: "Trial", color: CHART_COLORS.yellow, kind: "line" },
];

// === Consumption ===

export const SPEND_TREND_SERIES: XySeriesDef[] = [
  { field: "spend", name: "Spend", color: CHART_COLORS.blue, kind: "line" },
];

export const USAGE_COVERAGE_SERIES: XySeriesDef[] = [
  { field: "coverage", name: "Coverage", color: CHART_COLORS.blueLight, kind: "area" },
];

export const PROVIDER_TREND_SERIES: XySeriesDef[] = [
  { field: "azure", name: "Azure spend", color: CHART_COLORS.blue, kind: "area" },
  { field: "aws", name: "AWS spend", color: CHART_COLORS.navy, kind: "area" },
  { field: "gcp", name: "GCP spend", color: CHART_COLORS.yellow, kind: "area" },
];

export const TOP_ORGANIZATIONS_SERIES: XySeriesDef[] = [
  { field: "spend", name: "Monthly spend", color: CHART_COLORS.blue, kind: "column" },
];

export const COVERAGE_DONUT_COLORS = [CHART_COLORS.blue, CHART_COLORS.gray];
export const USAGE_DONUT_COLORS = [CHART_COLORS.navy, CHART_COLORS.gray];
