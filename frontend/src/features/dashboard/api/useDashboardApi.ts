import { useCallback, useMemo } from "react";

import consumptionMetrics from "../mock/consumption.json";
import maturityMetrics from "../mock/maturity.json";
import { ConsumptionMetrics, MaturityMetrics } from "./model";

// Stand-in for the aggregate endpoints the dashboard will eventually call — the backend
// has no spend-trend / coverage / maturity rollups yet. Keeping the same async callback
// shape as the real `useFooApi` hooks means swapping in HTTP later touches only this file.
export function useDashboardApi() {
  const getConsumptionMetrics = useCallback(
    async (): Promise<ConsumptionMetrics> => consumptionMetrics,
    [],
  );

  const getMaturityMetrics = useCallback(async (): Promise<MaturityMetrics> => maturityMetrics, []);

  return useMemo(
    () => ({ getConsumptionMetrics, getMaturityMetrics }),
    [getConsumptionMetrics, getMaturityMetrics],
  );
}
