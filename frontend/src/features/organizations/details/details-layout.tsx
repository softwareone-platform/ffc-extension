import { useEffect, useMemo } from 'react';

import { Outlet, useLocation, useNavigate, useParams, useResolvedPath } from 'react-router-dom';

import { Tab, Tabs } from '@swo/design-system/tabs';
import { OrganizationRead } from '@swo/ffc-api-model';

import { Status } from '~shared/components/entity-status-chip';
import { PageShell } from '~shared/components/page-shell';

import './details-layout.scss';

import { useOrganizationDetailsApi } from '~organizations/api';

const TABS: Array<{ id: string; label: string; segment: string }> = [
    { id: 'general', label: 'General', segment: 'general' },
    { id: 'data-sources', label: 'Data Sources', segment: 'data-sources' },
    { id: 'users', label: 'Users', segment: 'users' },
];

export function OrganizationDetailsLayout() {
    const { organizationId } = useParams();
    const basePath = useResolvedPath('').pathname.replace(/\/$/, '');
    const parentPath = basePath.replace(/\/[^/]+$/, '') || '/';
    const { data: entity } = useOrganizationDetailsApi(organizationId);
    const navigate = useNavigate();
    const { pathname } = useLocation();

    useEffect(() => {
        console.log(entity);
    }, [entity]);

    const tabs = useMemo(
        () =>
            TABS.map(({ id, label, segment }) => ({
                id,
                label,
                path: `${basePath}/${segment}`,
            })),
        [basePath],
    );

    const selectedTabId =
        tabs
            .filter((t) => pathname === t.path || pathname.startsWith(`${t.path}/`))
            .sort((a, b) => b.path.length - a.path.length)[0]?.id ??
        tabs[0]?.id ??
        '';

    const title = (
        <span className="organization-details-title">
            {entity?.id}
            {entity?.id && <Status<OrganizationRead> item={entity} />}
        </span>
    );

    return (
        <PageShell>
            <PageShell.Header
                backUrl={parentPath}
                title={title}
                subtitle={entity?.name ? `Organization ${entity.name}` : 'Organization details'}
                avatar={{
                    type: 'text',
                    shape: 'circle',
                    text: entity?.name ?? '?',
                    isToUseJdenticon: true,
                    jdenticonValue: entity?.id ?? entity?.name ?? '',
                }}
            />
            <PageShell.Content>
                <Tabs
                    selectedTabId={selectedTabId}
                    onTabChange={(id) => {
                        const target = tabs.find((t) => t.id === id);
                        if (target) navigate(target.path);
                    }}
                >
                    {tabs.map((tab) => (
                        <Tab key={tab.id} id={tab.id} title={tab.label}>
                            <Tab.Content>
                                {tab.id === selectedTabId ? <Outlet /> : null}
                            </Tab.Content>
                        </Tab>
                    ))}
                </Tabs>
            </PageShell.Content>
        </PageShell>
    );
}
