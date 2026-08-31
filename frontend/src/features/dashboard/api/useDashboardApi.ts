import { useCallback, useMemo } from "react";

import { AxiosResponse } from "axios";

import { mockResponse } from "~shared/utils/mockResponse";

import consumptionMetrics from "../mock/consumption.json";
import maturityMetrics from "../mock/maturity.json";
import { ConsumptionMetrics, MaturityMetrics } from "./model";

// Stand-in for the aggregate endpoints the dashboard will eventually call — the backend has
// no spend-trend / coverage / maturity rollups yet. Returns axios-shaped responses via
// `mockResponse`, so swapping in real HTTP later touches only this file.
export function useDashboardApi() {
  const getConsumptionMetrics = useCallback(
    (): Promise<AxiosResponse<ConsumptionMetrics>> => mockResponse(consumptionMetrics),
    [],
  );

  const getMaturityMetrics = useCallback(
    (): Promise<AxiosResponse<MaturityMetrics>> => mockResponse(maturityMetrics),
    [],
  );

  return useMemo(
    () => ({ getConsumptionMetrics, getMaturityMetrics }),
    [getConsumptionMetrics, getMaturityMetrics],
  );
}
