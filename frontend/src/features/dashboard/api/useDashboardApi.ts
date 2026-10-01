import { useCallback, useMemo } from "react";

import { AxiosResponse } from "axios";

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
  BILLING_STATUSES,
  BillingStatus,
  ConsumptionMetrics,
  MaturityMetrics,
} from "./model";

function isBillingStatus(value: string): value is BillingStatus {
  return (BILLING_STATUSES as readonly string[]).includes(value);
}

// Picks like "active"/"terminated"/"deleted" don't exist on the orgs-without-datasources rows,
// so a selection that contains none of {paid, trial} is treated as "no billing filter" rather
// than "no results".
function filterAdoption(data: AdoptionMetrics, filters: DashboardFilters): AdoptionMetrics {
  const billingPicks = filters.statuses.filter(isBillingStatus);
  if (billingPicks.length === 0) {
    return data;
  }
  return {
    ...data,
    organizationsWithoutDatasources: data.organizationsWithoutDatasources.filter((row) =>
      billingPicks.includes(row.status),
    ),
  };
}

export function useDashboardApi() {
  const getAdoptionMetrics = useCallback(
    (filters: DashboardFilters): Promise<AxiosResponse<AdoptionMetrics>> =>
      mockResponse(filterAdoption(adoptionMetrics as AdoptionMetrics, filters)),
    [],
  );

  // Consumption + maturity accept filters for signature uniformity but don't apply any mock-side
  // transform yet. Extend here when a stakeholder demo needs a specific chart to react.
  const getConsumptionMetrics = useCallback(
    (_filters: DashboardFilters): Promise<AxiosResponse<ConsumptionMetrics>> =>
      mockResponse(consumptionMetrics),
    [],
  );

  const getMaturityMetrics = useCallback(
    (_filters: DashboardFilters): Promise<AxiosResponse<MaturityMetrics>> =>
      mockResponse(maturityMetrics),
    [],
  );

  return useMemo(
    () => ({ getAdoptionMetrics, getConsumptionMetrics, getMaturityMetrics }),
    [getAdoptionMetrics, getConsumptionMetrics, getMaturityMetrics],
  );
}
