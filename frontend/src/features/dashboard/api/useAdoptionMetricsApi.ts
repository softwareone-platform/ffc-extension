import { useQuery } from "@tanstack/react-query";

import { useDashboardApi } from "./useDashboardApi";

export function useAdoptionMetricsApi() {
  const { getAdoptionMetrics } = useDashboardApi();

  return useQuery({
    queryKey: ["Dashboard", "AdoptionMetrics"] as const,
    queryFn: async () => (await getAdoptionMetrics()).data,
  });
}
