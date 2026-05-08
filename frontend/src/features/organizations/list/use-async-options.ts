import { useOrganizationsApi } from '../api/use-organizations-api';
import { useReactQueryRqlGrid } from '~shared/hooks/use-react-query-rql-grid';
import { OrganizationRead } from '@swo/ffc-api-model';
import { Entity } from '@swo/service';

export interface AxiosResponseData<T> {
    data: T | null;
}

export interface ListResponse<T> {
    total: number;
    offset?: number;
    limit?: number;
    items?: Array<T>;
}

function ensureArray<TArray extends unknown[]>(value: TArray | undefined | null): TArray {
    if (!value) {
        return [] as unknown as TArray;
    }
    return value;
}

export function mapAxiosResponseDataList<T>(res: AxiosResponseData<ListResponse<T>>) {
    const offset = res?.data?.offset ?? 0;
    const limit = res?.data?.limit ?? 0;
    const total = res?.data?.total;
    const data = ensureArray(res?.data?.items);

    if (limit && data.length < limit && total === undefined) {
        return { data, total: offset + data.length };
    }
    return { data, total: total ?? undefined };
}

export function useAsyncOptions() {
    const { list } = useOrganizationsApi();
    const baseQueryKey = ['Organizations'] as const;
    return useReactQueryRqlGrid<Entity<OrganizationRead>, Awaited<ReturnType<typeof list>>>(
        baseQueryKey,
        (query) => ({
            queryKey: [...baseQueryKey, query.toString()] as const,
            queryFn: () => list(query),
            select: mapAxiosResponseDataList,
        }),
    );
}
