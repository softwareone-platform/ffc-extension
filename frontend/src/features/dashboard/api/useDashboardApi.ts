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
  const dateScale = rangeMonths(filters) / BASELINE_MONTHS;
  return statusScale * providerScale * dateScale;
}

// Full-month count of the selected range: a 1 Sep → 30 Sep window is 1 month, a 1 Jul → 30 Sep
// window is 3, etc. `differenceInCalendarMonths` is boundary-based (would return 0 for a
// same-month range), so we add 1 to count the start month as well.
function rangeMonths(filters: DashboardFilters): number {
  return Math.max(1, differenceInCalendarMonths(filters.to, filters.from) + 1);
}

// Number of monthly chart points to render — the actual range length, capped at the mock's
// 12-month ceiling. A 1-month range → 1 bar, a 4-month range → 4 bars, 12 months → 12 bars.
function monthWindow(filters: DashboardFilters): number {
  return Math.min(12, rangeMonths(filters));
}

const MONTHLY_CATEGORIES = new Set(["month", "period", "bucket"]);

// Deeply clone the mock object while multiplying numeric fields by `scale` and tailing monthly
// chart arrays to the last `monthWindow` entries. Supports:
//   - raw numbers         → scaled integer
//   - "412" / "1,234"     → scaled integer, formatted with thousands separator
//   - "$1,250"            → preserved prefix, scaled integer, re-formatted
//   - "98%" / "-1.2%"     → left alone (percentages are ratios, not totals)
//   - everything else     → left alone (labels, categories, IDs, dates)
function transformMetrics<T>(value: T, scale: number, months: number): T {
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

// The status donut shows ratios between Active / Terminated / Deleted — a uniform scale
// multiplier keeps those ratios identical, so the user sees "no change". After the generic
// transform, zero out the slices and per-status KPIs that aren't in the filter picks and
// recompute `total` from the remaining slices, so the donut and headline react visibly.
const ORG_STATUS_CATEGORIES = ["active", "terminated", "deleted"] as const;
const BILLING_STATUS_CATEGORIES = ["paid", "trial"] as const;

function filterOrgStatusView(data: AdoptionMetrics, filters: DashboardFilters): AdoptionMetrics {
  const orgPicks = filters.statuses.filter((status) =>
    (ORG_STATUS_CATEGORIES as readonly string[]).includes(status),
  );
  // No org-status pick (empty or billing-only) → the distribution is orthogonal, leave it.
  if (orgPicks.length === 0 || orgPicks.length === ORG_STATUS_CATEGORIES.length) {
    return data;
  }
  const includes = (slice: string) =>
    orgPicks.includes(slice.toLowerCase() as (typeof ORG_STATUS_CATEGORIES)[number]);

  const nextDistribution = data.organizationsOverview.statusDistribution.map((slice) => ({
    ...slice,
    value: includes(slice.category) ? slice.value : 0,
  }));
  const nextTotal = nextDistribution.reduce((sum, slice) => sum + slice.value, 0);

  return {
    ...data,
    organizationsOverview: {
      ...data.organizationsOverview,
      total: nextTotal.toLocaleString("en-US"),
      active: includes("active") ? data.organizationsOverview.active : "0",
      terminated: includes("terminated") ? data.organizationsOverview.terminated : "0",
      deleted: includes("deleted") ? data.organizationsOverview.deleted : "0",
      statusDistribution: nextDistribution,
    },
  };
}

// Provider-breakdown views (stacked column, per-provider donut, per-provider trend) share the
// same shape: either a row like `{ period, azure, aws, gcp }` or a slice like
// `{ category: "Azure", value: … }`. Walking the whole payload and zeroing out non-selected
// provider keys makes "pick Azure only" visibly leave Azure as the sole series/slice.
function filterProviderView<T>(data: T, filters: DashboardFilters): T {
  if (filters.providers.length === 0 || filters.providers.length === CLOUD_PROVIDERS.length) {
    return data;
  }
  const picks = new Set<string>(filters.providers);
  return walkProviderView(data, picks) as T;
}

function walkProviderView(value: unknown, picks: Set<string>): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => walkProviderView(item, picks));
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    // Distribution slice shape: `{ category, value }` — drop the slice if its category is a
    // provider name that wasn't picked.
    const category = entries.find(([key]) => key === "category")?.[1];
    if (typeof category === "string") {
      const matchedProvider = (CLOUD_PROVIDERS as readonly string[]).find(
        (provider) => provider.toLowerCase() === category.toLowerCase(),
      );
      if (matchedProvider && !picks.has(matchedProvider)) {
        return { ...value, value: 0 };
      }
    }
    const out: Record<string, unknown> = {};
    for (const [key, nested] of entries) {
      // Row shape: `{ period, azure, aws, gcp }` — zero out the per-provider columns the
      // user hasn't selected so stacked bars collapse to the picked providers.
      if ((CLOUD_PROVIDERS as readonly string[]).includes(key) && !picks.has(key)) {
        out[key] = typeof nested === "number" ? 0 : nested;
      } else {
        out[key] = walkProviderView(nested, picks);
      }
    }
    return out;
  }
  return value;
}

// Mirror of `filterOrgStatusView` for the Trial vs Paid panel. When the user picks only one
// of the billing statuses, zero out the other series/slice so the donut and the monthly
// trend chart collapse to the picked side.
function filterTrialVsPaidView(data: AdoptionMetrics, filters: DashboardFilters): AdoptionMetrics {
  const billingPicks = filters.statuses.filter((status) =>
    (BILLING_STATUS_CATEGORIES as readonly string[]).includes(status),
  );
  if (
    billingPicks.length === 0 ||
    billingPicks.length === BILLING_STATUS_CATEGORIES.length
  ) {
    return data;
  }
  const paidPicked = billingPicks.includes("paid");
  const trialPicked = billingPicks.includes("trial");

  const nextDistribution = data.trialVsPaid.distribution.map((slice) => {
    const key = slice.category.toLowerCase();
    const visible = (key === "paid" && paidPicked) || (key === "trial" && trialPicked);
    return { ...slice, value: visible ? slice.value : 0 };
  });

  const nextTrend = data.trialVsPaid.monthlyTrend.map((row) => ({
    ...row,
    paid: paidPicked ? row.paid : 0,
    trial: trialPicked ? row.trial : 0,
  }));

  return {
    ...data,
    trialVsPaid: {
      ...data.trialVsPaid,
      paid: paidPicked ? data.trialVsPaid.paid : "0",
      trial: trialPicked ? data.trialVsPaid.trial : "0",
      distribution: nextDistribution,
      monthlyTrend: nextTrend,
    },
  };
}

export function useDashboardApi() {
  const getAdoptionMetrics = useCallback(
    (filters: DashboardFilters): Promise<AxiosResponse<AdoptionMetrics>> => {
      const scaled = transformMetrics(
        adoptionMetrics as AdoptionMetrics,
        computeScale(filters),
        monthWindow(filters),
      );
      const filtered = filterProviderView(
        filterTrialVsPaidView(filterOrgStatusView(scaled, filters), filters),
        filters,
      );
      return mockResponse(filtered, MOCK_DELAY_MS);
    },
    [],
  );

  const getConsumptionMetrics = useCallback(
    (filters: DashboardFilters): Promise<AxiosResponse<ConsumptionMetrics>> => {
      const scaled = transformMetrics(
        consumptionMetrics as ConsumptionMetrics,
        computeScale(filters),
        monthWindow(filters),
      );
      return mockResponse(filterProviderView(scaled, filters), MOCK_DELAY_MS);
    },
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
