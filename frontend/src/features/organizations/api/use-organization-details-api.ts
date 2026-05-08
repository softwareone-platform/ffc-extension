import { useQuery } from '@tanstack/react-query';

import { useOrganizationsApi } from './use-organizations-api';

export function useOrganizationDetailsApi(organizationId: string | undefined) {
    const { get } = useOrganizationsApi();
    return useQuery({
        queryKey: ['Organizations', 'Details', organizationId] as const,
        queryFn: () => get(organizationId!),
        select: (res) => res.data,
        enabled: Boolean(organizationId),
    });
}
