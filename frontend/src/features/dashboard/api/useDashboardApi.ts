import { useCallback, useMemo } from "react";

import { AxiosResponse } from "axios";
import { differenceInCalendarMonths } from "date-fns";

import { mockResponse } from "~shared/utils/mockResponse";

// Real-API swap seam. `mockResponse(json)` returns the same `AxiosResponse<T>` shape as
// `http<T>({ method: "GET", url })` from `@mpt-extension/sdk` (see useEntitlementsApi.tsx),
// so each getter body is a one-line swap:
//   mockResponse(adoptionMetrics as AdoptionMetrics)
//     → http<AdoptionMetrics>({ method: "GET", url: `/ops/v1/dashboard/adoption?${qs(filters)}` })
// The getter signatures stay stable, so metricsQueries.ts and the tabs don't change.

import { DashboardFilters } from "../components/DashboardFiltersContext";
import adoptionMetrics from "../mock/adoption.json";
import consumptionMetrics from "../mock/consumption.json";
import maturityMetrics from "../mock/maturity.json";
import {
  AdoptionMetrics,
  CLOUD_PROVIDERS,
  CloudProvider,
  ConsumptionMetrics,
  MaturityMetrics,
  ORGANISATION_STATUSES,
  OrganisationStatus,
} from "./model";

// 600 ms is slow enough that the dashboard loading overlay is visibly present on filter
// changes — demos the "fetching new data" affordance without feeling broken.
const MOCK_DELAY_MS = 600;

// Approximate population share for each dimension. Multiplying selected shares gives a scalar
// that scales every numeric field in the mock responses — enough for a stakeholder demo where
// the whole dashboard visibly reacts to filter changes.
const STATUS_SHARE: Record<OrganisationStatus, number> = {
  active: 0.6,
  paid: 0.2,
  trial: 0.1,
  terminated: 0.07,
  deleted: 0.03,
};

const PROVIDER_SHARE: Record<CloudProvider, number> = {
  azure: 0.46,
  aws: 0.33,
  gcp: 0.21,
};

// Baseline date-range window used to normalise the mock. The provider seeds filters with a
// 3-month range, so a user who hasn't touched the date picker sees unscaled mock values.
const BASELINE_MONTHS = 3;

function computeScale(filters: DashboardFilters): number {
  const statusScale =
    filters.statuses.length === 0 || filters.statuses.length === ORGANISATION_STATUSES.length
      ? 1
      : filters.statuses.reduce((sum, status) => sum + STATUS_SHARE[status], 0);
  const providerScale =
    filters.providers.length === 0 || filters.providers.length === CLOUD_PROVIDERS.length
      ? 1
      : filters.providers.reduce((sum, provider) => sum + PROVIDER_SHARE[provider], 0);
  // Date range scales every numeric field proportionally to its length: a shorter window
  // reads as "less activity", a longer window as "more". `BASELINE_MONTHS` keeps the default
  // range at 1× so the mock numbers match the JSON on first load.
  const months = Math.max(1, differenceInCalendarMonths(filters.to, filters.from));
  const dateScale = months / BASELINE_MONTHS;
  return statusScale * providerScale * dateScale;
}

// Short ranges (< 6 months) collapse chart data to the last 3 points so narrow windows read
// as "compact"; longer ranges keep the full 6-point series. The user-visible effect is that
// picking a shorter preset or custom range makes every monthly chart redraw with fewer bars.
function monthWindow(filters: DashboardFilters): 3 | 6 {
  return differenceInCalendarMonths(filters.to, filters.from) < 6 ? 3 : 6;
}

const MONTHLY_CATEGORIES = new Set(["month", "period", "bucket"]);

// Deeply clone the mock object while multiplying numeric fields by `scale` and tailing monthly
// chart arrays to the last `monthWindow` entries. Supports:
//   - raw numbers         → scaled integer
//   - "412" / "1,234"     → scaled integer, formatted with thousands separator
//   - "$1,250"            → preserved prefix, scaled integer, re-formatted
//   - "98%" / "-1.2%"     → left alone (percentages are ratios, not totals)
//   - everything else     → left alone (labels, categories, IDs, dates)
function transformMetrics<T>(value: T, scale: number, months: 3 | 6): T {
  if (typeof value === "number") {
    return Math.round(value * scale) as T;
  }
  if (typeof value === "string") {
    const currencyMatch = value.match(/^\$([\d,]+(?:\.\d+)?)$/);
    if (currencyMatch) {
      const num = Number(currencyMatch[1].replace(/,/g, ""));
      return `$${Math.round(num * scale).toLocaleString("en-US")}` as unknown as T;
    }
    const integerMatch = value.match(/^-?\d{1,3}(?:,\d{3})*$/) || value.match(/^-?\d+$/);
    if (integerMatch) {
      const num = Number(value.replace(/,/g, ""));
      return Math.round(num * scale).toLocaleString("en-US") as unknown as T;
    }
    return value;
  }
  if (Array.isArray(value)) {
    const mapped = value.map((item) => transformMetrics(item, scale, months));
    // Monthly chart arrays carry a `month`/`period`/`bucket` key on each row — tail to the
    // requested window so date-range changes visibly redraw.
    const isMonthlySeries =
      mapped.length > 0 &&
      typeof mapped[0] === "object" &&
      mapped[0] !== null &&
      !Array.isArray(mapped[0]) &&
      Object.keys(mapped[0]).some((key) => MONTHLY_CATEGORIES.has(key));
    const sliced = isMonthlySeries ? mapped.slice(-months) : mapped;
    return sliced as unknown as T;
  }
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, nested] of Object.entries(value)) {
      out[key] = transformMetrics(nested, scale, months);
    }
    return out as T;
  }
  return value;
}

export function useDashboardApi() {
  const getAdoptionMetrics = useCallback(
    (filters: DashboardFilters): Promise<AxiosResponse<AdoptionMetrics>> =>
      mockResponse(
        transformMetrics(adoptionMetrics as AdoptionMetrics, computeScale(filters), monthWindow(filters)),
        MOCK_DELAY_MS,
      ),
    [],
  );

  const getConsumptionMetrics = useCallback(
    (filters: DashboardFilters): Promise<AxiosResponse<ConsumptionMetrics>> =>
      mockResponse(
        transformMetrics(consumptionMetrics as ConsumptionMetrics, computeScale(filters), monthWindow(filters)),
        MOCK_DELAY_MS,
      ),
    [],
  );

  const getMaturityMetrics = useCallback(
    (filters: DashboardFilters): Promise<AxiosResponse<MaturityMetrics>> =>
      mockResponse(
        transformMetrics(maturityMetrics as MaturityMetrics, computeScale(filters), monthWindow(filters)),
        MOCK_DELAY_MS,
      ),
    [],
  );

  return useMemo(
    () => ({ getAdoptionMetrics, getConsumptionMetrics, getMaturityMetrics }),
    [getAdoptionMetrics, getConsumptionMetrics, getMaturityMetrics],
  );
}
