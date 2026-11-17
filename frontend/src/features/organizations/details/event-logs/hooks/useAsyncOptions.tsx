import { OrganizationEventRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~features/organizations/api";
import { useReactQueryRqlGrid } from "~shared/hooks/useReactQueryRqlGrid";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";

export function useAsyncOptions(organizationId: string) {
  const { listOrganizationLogs } = useOrganizationsApi();
  const baseQueryKey: unknown[] = ["OrganizationLogs", organizationId];
  return useReactQueryRqlGrid<
    OrganizationEventRead,
    Awaited<ReturnType<typeof listOrganizationLogs>>
  >(baseQueryKey, (query) => ({
    queryKey: [baseQueryKey, query.toString(), organizationId],
    queryFn: () => listOrganizationLogs(organizationId, query),
    select: mapAxiosResponseDataList,
  }));
}
