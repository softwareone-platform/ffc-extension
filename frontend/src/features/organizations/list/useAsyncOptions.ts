import { OrganizationRead } from "@swo/ffc-api-model";
import { Entity } from "@swo/service";

import { useOrganizationsApi } from "~organizations/api";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

export function useAsyncOptions() {
  const { list } = useOrganizationsApi();
  const baseQueryKey = ["Organizations"] as const;
  return useReactQueryRqlGrid<Entity<OrganizationRead>, Awaited<ReturnType<typeof list>>>(
    baseQueryKey,
    (query) => ({
      queryKey: [...baseQueryKey, query.toString()] as const,
      queryFn: () => list(query),
      select: mapAxiosResponseDataList,
    }),
  );
}
