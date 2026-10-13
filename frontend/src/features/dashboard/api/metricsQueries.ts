import { AxiosResponse } from "axios";
import { keepPreviousData, useQuery } from "@tanstack/react-query";

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
      // Keep the previous payload rendered while the next one is in flight — prevents the
      // `if (!data) return null` guard in each tab from unmounting the whole panel grid
      // (amCharts restarts its load animation on remount) every time a filter changes.
      placeholderData: keepPreviousData,
    });
  };
}

export const useAdoptionMetricsApi = createMetricsQuery("AdoptionMetrics", (api) => api.getAdoptionMetrics);
export const useConsumptionMetricsApi = createMetricsQuery("ConsumptionMetrics", (api) => api.getConsumptionMetrics);
export const useMaturityMetricsApi = createMetricsQuery("MaturityMetrics", (api) => api.getMaturityMetrics);
