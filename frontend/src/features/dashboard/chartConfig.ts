import { CHART_COLORS, XySeriesDef } from "~shared/components/charts";

import { BillingStatus, CloudProvider, OrganisationStatus } from "./api/model";

/**
 * Canonical chart heights for the dashboard. The scale is intentionally small —
 * if a new value is needed, extend here rather than inlining a magic number.
 */
export const CHART_HEIGHT = { xs: 190, sm: 200, md: 220, lg: 260 } as const;

// === Adoption ===

// Unified status palette across the whole dashboard: Active → green, Terminated → gray,
// Deleted → red (organisation status) and Paid → orange, Trial → yellow (billing status, see
// `BILLING_COLOR`). Keep this mapping consistent anywhere a status is coloured so the colour
// alone tells the user which status they're looking at.
export const STATUS_COLOR: Record<OrganisationStatus, number> = {
  active: CHART_COLORS.green,
  terminated: CHART_COLORS.gray,
  deleted: CHART_COLORS.red,
};

// Billing swatches for the filter multi-select and the Trial vs Paid panel.
export const BILLING_COLOR: Record<BillingStatus, number> = {
  paid: CHART_COLORS.orange,
  trial: CHART_COLORS.yellow,
};

// Provider swatches shown in the filter multi-select. Values mirror `DATASOURCE_PROVIDER_SERIES`
// and `PROVIDER_TREND_SERIES` below.
export const PROVIDER_COLOR: Record<CloudProvider, number> = {
  azure: CHART_COLORS.blue,
  aws: CHART_COLORS.navy,
  gcp: CHART_COLORS.yellow,
};

export const STATUS_LEGEND_KEYS = ["active", "terminated", "deleted"] as const;
export const STATUS_DONUT_COLORS = [
  STATUS_COLOR.active,
  STATUS_COLOR.terminated,
  STATUS_COLOR.deleted,
];

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

// Order matches `trialVsPaid.distribution` in `adoption.json` (Paid first, Trial second).
export const TRIAL_VS_PAID_DONUT_COLORS = [BILLING_COLOR.paid, BILLING_COLOR.trial];

export const TRIAL_VS_PAID_TREND_SERIES: XySeriesDef[] = [
  { field: "paid", name: "Paid", color: BILLING_COLOR.paid, kind: "line" },
  { field: "trial", name: "Trial", color: BILLING_COLOR.trial, kind: "line" },
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
