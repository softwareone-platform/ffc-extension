import { useQuery } from '@tanstack/react-query';

import { useEntitlementsApi } from './useEntitlementsApi';

export function useEntitlementsDetailsApi(entitlementId: string | undefined) {
    const { get } = useEntitlementsApi();
    return useQuery({
        queryKey: ['Entitlements', 'Details', entitlementId] as const,
        queryFn: () => get(entitlementId!),
        select: (res) => res.data,
        enabled: Boolean(entitlementId),
    });
}
