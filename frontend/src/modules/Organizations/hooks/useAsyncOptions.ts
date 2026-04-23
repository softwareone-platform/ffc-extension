// import { mapAxiosResponseDataList } from "@/Modules/Shared/ReactQueryUtils";
// import { Journal } from "@/api/TemporaryApiModel";
// import { useBaseQueryKey } from '@/api/useBaseQueryKey';
// import { useJournalApi } from '@/api/useJournalApi';
// import { useReactQueryRqlGrid } from '@/api/useReactQueryRqlGrid';
import { useOrganizationsApi } from "./useOrganizationsApi";
import { useReactQueryRqlGrid } from "../../../shared/hooks/useReactQueryRqlGrid";
import { OrganizationRead } from "@swo/ffc-api-model";
import { Entity } from "@swo/service";

import { AxiosError, AxiosResponse } from "axios";

export interface AxiosResponseData<T> {
  data: T | null;
  //   error: AxiosError | string | null;
}

export interface ListResponse<T> {
  total: number;
  offset?: number;
  limit?: number;
  items?: Array<T>;
}

export function ensureArray<TArray extends unknown[]>(
  value: TArray | undefined | null,
): TArray {
  if (!value) {
    return [] as unknown as TArray;
  }
  return value;
}

export function mapAxiosResponseDataList<T>(
  res: AxiosResponseData<ListResponse<T>>,
) {
  const offset = res?.data?.offset ?? 0;
  const limit = res?.data?.limit ?? 0;
  const total = res?.data?.total;
  const data = ensureArray(res?.data?.items);

  console.log("Mapping response data...", { offset, limit, total, data, res });
  if (limit && data.length < limit && total === undefined) {
    return { data, total: offset + data.length };
  }
  return { data: data, total: total ?? undefined };
}

export function useAsyncOptions() {
  //   const { list } = useJournalApi();
  const { list } = useOrganizationsApi();
  const baseQueryKey: any = "Organizations"; //useBaseQueryKey('Journal');
  return useReactQueryRqlGrid<
    Entity<OrganizationRead>,
    Awaited<ReturnType<typeof list>>
  >(baseQueryKey, (query) => ({
    queryKey: [baseQueryKey, query.toString()],
    queryFn: () => list(query),
    select: mapAxiosResponseDataList,
  }));
}
