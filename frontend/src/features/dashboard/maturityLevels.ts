import { CHART_COLORS, XySeriesDef } from "~shared/components/charts";

/**
 * Presentation config for the five FinOps maturity levels: `key` is both the i18n key
 * suffix (`dashboard:maturity:levels:<key>`) and the numeric field name in the maturity
 * JSON, so the legend, donut, charts and table all stay colour-consistent.
 */
export const MATURITY_LEVELS = [
  { level: 0, key: "registered", color: CHART_COLORS.gray },
  { level: 1, key: "connected", color: CHART_COLORS.blue },
  { level: 2, key: "visible", color: CHART_COLORS.yellow },
  { level: 3, key: "optimizing", color: CHART_COLORS.orange },
  { level: 4, key: "operationalized", color: CHART_COLORS.green },
];

export const MATURITY_COLORS = MATURITY_LEVELS.map((entry) => entry.color);

export const MATURITY_AREA_SERIES: XySeriesDef[] = MATURITY_LEVELS.map((entry) => ({
  field: entry.key,
  name: `Level ${entry.level}`,
  color: entry.color,
  kind: "area",
}));

export const MATURITY_COLUMN_SERIES: XySeriesDef[] = MATURITY_LEVELS.map((entry) => ({
  field: entry.key,
  name: `Level ${entry.level}`,
  color: entry.color,
  kind: "column",
}));
