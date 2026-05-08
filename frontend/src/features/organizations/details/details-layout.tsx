import { Card } from '@swo/design-system/card';
import { Navigation } from '@swo/design-system/navigation';
import { Link, Outlet, useParams, useResolvedPath } from 'react-router-dom';
import { useEffect, useMemo } from 'react';
import { OrganizationRead } from '@swo/ffc-api-model';
import { Status } from '~shared/components/entity-status-chip';
import { useOrganizationDetailsApi } from '../api/use-organization-details-api';

/**
 * Tabs declared once here — child route modules render the panels.
 * Keeping the list co-located with the layout avoids duplicated knowledge
 * and lets `Navigation.TopBar` render before any child module loads.
 */
const TABS: Array<{ label: string; segment: string }> = [
    { label: 'General', segment: 'general' },
    { label: 'Data Sources', segment: 'data-sources' },
    { label: 'Users', segment: 'users' },
];

/**
 * Layout for the Organization Details page. Fetches the organization, renders
 * the header + sticky tab bar, and slots the active sub-route via `<Outlet />`.
 *
 * Mount-point agnostic: uses `useResolvedPath('')` so it works wherever it's
 * routed (standalone bundle or under a host prefix).
 */
export function OrganizationDetailsLayout() {
    const { organizationId } = useParams();
    const basePath = useResolvedPath('').pathname.replace(/\/$/, '');
    const { data: entity } = useOrganizationDetailsApi(organizationId);

    useEffect(() => {
        console.log(entity);
    }, [entity]);

    const tabs = useMemo(
        () =>
            TABS.map((tab) => ({
                label: tab.label,
                path: `${basePath}/${tab.segment}`,
            })),
        [basePath],
    );

    return (
        <>
            <Card className={'organization-details-header'}>
                {entity && entity.id && (
                    <>
                        <h1>{entity.name}</h1>
                        <Status<OrganizationRead> item={entity} />
                    </>
                )}
                {/* Relative `..` goes up to the Organizations list, regardless of mount point. */}
                <Link to={'..'} relative="path">
                    Back
                </Link>
            </Card>
            <Navigation.TopBar items={tabs} />
            <Card>
                <Outlet />
            </Card>
        </>
    );
}
