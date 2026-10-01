import { useCallback, useMemo } from "react";

import { AxiosResponse } from "axios";

import { mockResponse } from "~shared/utils/mockResponse";

import adoptionMetrics from "../mock/adoption.json";
import consumptionMetrics from "../mock/consumption.json";
import maturityMetrics from "../mock/maturity.json";
import { AdoptionMetrics, ConsumptionMetrics, MaturityMetrics } from "./model";

export function useDashboardApi() {
  const getAdoptionMetrics = useCallback(
    (): Promise<AxiosResponse<AdoptionMetrics>> => mockResponse(adoptionMetrics as AdoptionMetrics),
    [],
  );

  const getConsumptionMetrics = useCallback(
    (): Promise<AxiosResponse<ConsumptionMetrics>> => mockResponse(consumptionMetrics),
    [],
  );

  const getMaturityMetrics = useCallback(
    (): Promise<AxiosResponse<MaturityMetrics>> => mockResponse(maturityMetrics),
    [],
  );

  return useMemo(
    () => ({ getAdoptionMetrics, getConsumptionMetrics, getMaturityMetrics }),
    [getAdoptionMetrics, getConsumptionMetrics, getMaturityMetrics],
  );
}
