import { EntitlementRead } from '@swo/ffc-api-model';
import { EntityReferenceCell } from '@swo/design-system/entity-reference-cell';
import { InPageHighlight } from '@swo/design-system/in-page-highlight';
import {
    Outlet,
    useLocation,
    useNavigate,
    useParams,
    useResolvedPath
    } from 'react-router-dom';
import { Tab, Tabs } from '@swo/design-system/tabs';
import { useEffect, useMemo } from 'react';
import './DetailsLayout.scss';
import { Status } from '~shared/components/entity-status-chip';
import { PageShell } from '~shared/components/page-shell';

import { useFixedT } from "~shared/hooks/useFixedT";
import { useEntitlementsDetailsApi } from '~entitlements/api';
import DataSourceIcon from '~shared/components/data-source-icons/DataSourceIcon';
import { Navigation } from "@swo/design-system/navigation";

const TABS: Array<{ id: string; label: string; segment: string }> = [
    { id: 'general', label: 'General', segment: 'general' }
];

export function EntitlementsDetailsLayout() {
    const { entitlementId } = useParams();
    const basePath = useResolvedPath('').pathname.replace(/\/$/, '');
    const parentPath = basePath.replace(/\/[^/]+$/, '') || '/';
    const { data: entity } = useEntitlementsDetailsApi(entitlementId);
    const navigate = useNavigate();
    
    const { pathname } = useLocation();
    const tProperties = useFixedT("shared:grid:columns");

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
        <span className="entitlement-details-title">
            {entity?.id}
            {entity?.id && <Status<EntitlementRead> item={entity} />}
        </span>
    );

    return (
        <PageShell>
            <PageShell.Header
                backUrl={parentPath}
                title={title}
                subtitle={entity?.name ? `Entitlement ${entity.name}` : 'Entitlement details'}
                avatar={{
                    type: 'text',
                    shape: 'circle',
                    text: entity?.name ?? '?',
                    isToUseJdenticon: true,
                    jdenticonValue: entity?.id ?? entity?.name ?? '',
                }}
            />
            <PageShell.Content>
                  <Navigation.Highlights>
                    {entity && entity.id && (
                    <InPageHighlight style="inline">
                        <InPageHighlight.Item title={tProperties("affiliate_external_id")}>
                        <EntityReferenceCell
                            primaryContent={entity.owner.name}
                            secondaryContent={entity.owner.id}
                        />
                        </InPageHighlight.Item>
                        <InPageHighlight.Item title={tProperties("data_source")}>
                        {entity.linked_datasource_id && (
                            <EntityReferenceCell
                            primaryContent={entity.linked_datasource_name as string}
                            secondaryContent={entity.linked_datasource_id as string}
                            secondaryContentMaxHeight={50}
                            icon={
                                <DataSourceIcon
                                name={entity.linked_datasource_type as string}
                                size={48}
                                />
                            }
                            />
                        )}
                        </InPageHighlight.Item>
                        <InPageHighlight.Item title={tProperties("organization")}>
                        {entity.events.redeemed && (
                            <EntityReferenceCell
                            primaryContent={entity.events.redeemed?.by.name}
                            secondaryContent={entity.events.redeemed?.by.id}
                            />
                        )}
                        </InPageHighlight.Item>
                    </InPageHighlight>
                    )}
                </Navigation.Highlights>
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
