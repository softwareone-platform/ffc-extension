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
import { AdoptionMetrics, ConsumptionMetrics, MaturityMetrics } from "./model";

export function useDashboardApi() {
  // Each getter accepts the filter payload for signature uniformity, but the mock responses
  // don't apply any transform yet. Extend here when a stakeholder demo needs a specific chart
  // to react.
  const getAdoptionMetrics = useCallback(
    (_filters: DashboardFilters): Promise<AxiosResponse<AdoptionMetrics>> =>
      mockResponse(adoptionMetrics as AdoptionMetrics),
    [],
  );

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
