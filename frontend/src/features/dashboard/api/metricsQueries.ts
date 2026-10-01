import { AxiosResponse } from "axios";
import { useQuery } from "@tanstack/react-query";

import { DashboardFilters, useDashboardFilters } from "../components/DashboardFiltersContext";
import { useDashboardApi } from "./useDashboardApi";

type DashboardApi = ReturnType<typeof useDashboardApi>;
type Fetcher<T> = (filters: DashboardFilters) => Promise<AxiosResponse<T>>;

function createMetricsQuery<T>(key: string, select: (api: DashboardApi) => Fetcher<T>) {
  return function useMetricsQuery() {
    const { filters } = useDashboardFilters();
    const fetcher = select(useDashboardApi());
    return useQuery({
      queryKey: ["Dashboard", key, filters] as const,
      queryFn: async () => (await fetcher(filters)).data,
    });
  };
}

export const useAdoptionMetricsApi = createMetricsQuery("AdoptionMetrics", (api) => api.getAdoptionMetrics);
export const useConsumptionMetricsApi = createMetricsQuery("ConsumptionMetrics", (api) => api.getConsumptionMetrics);
export const useMaturityMetricsApi = createMetricsQuery("MaturityMetrics", (api) => api.getMaturityMetrics);
