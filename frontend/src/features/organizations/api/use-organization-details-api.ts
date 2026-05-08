import { useQuery } from '@tanstack/react-query';
import { useOrganizationsApi } from './use-organizations-api';

/**
 * Fetch a single organization by id.
 *
 * Co-locates the react-query cache key (`['Organizations', 'Details', id]`)
 * with the request, so multiple consumers reading the same organization
 * (e.g. the details layout + the General tab) hit the same cache entry and
 * do not refetch.
 */
export function useOrganizationDetailsApi(organizationId: string | undefined) {
    const { get } = useOrganizationsApi();
    return useQuery({
        queryKey: ['Organizations', 'Details', organizationId] as const,
        queryFn: () => get(organizationId!),
        select: (res) => res.data,
        enabled: Boolean(organizationId),
    });
}
