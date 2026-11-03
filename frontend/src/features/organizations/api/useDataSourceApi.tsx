import { useQuery } from "@tanstack/react-query";

import { DatasourceDetailRead } from "~api/ffc-api-model";
import { useEntityApi } from "~shared/hooks/useEntityApi";

const rootPath = "/ops/v1/organizations";

export function useDataSourceApi(
  organizationId: string | undefined,
  dataSourceId: string | undefined,
) {
  const { get } = useEntityApi<DatasourceDetailRead>(`${rootPath}/${organizationId}/datasources`);

  return useQuery({
    queryKey: ["Organizations", "Details", organizationId, dataSourceId] as const,
    queryFn: () => get(dataSourceId!),
    select: (res) => res.data,
    enabled: Boolean(organizationId && dataSourceId),
  });
}
