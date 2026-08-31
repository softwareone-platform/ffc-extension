import { useQuery } from "@tanstack/react-query";

import { useDashboardApi } from "./useDashboardApi";

export function useMaturityMetricsApi() {
  const { getMaturityMetrics } = useDashboardApi();

  return useQuery({
    queryKey: ["Dashboard", "MaturityMetrics"] as const,
    queryFn: async () => (await getMaturityMetrics()).data,
  });
}
