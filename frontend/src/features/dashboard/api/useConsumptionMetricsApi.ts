import { useQuery } from "@tanstack/react-query";

import { useDashboardApi } from "./useDashboardApi";

export function useConsumptionMetricsApi() {
  const { getConsumptionMetrics } = useDashboardApi();

  return useQuery({
    queryKey: ["Dashboard", "ConsumptionMetrics"] as const,
    queryFn: getConsumptionMetrics,
  });
}
