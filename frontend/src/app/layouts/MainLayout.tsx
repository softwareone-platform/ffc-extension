import { useMemo, useState } from 'react';

import { Outlet, useMatch } from 'react-router-dom';

import { Button } from '@swo/design-system/button';

import { PATHS } from '~app/paths';
import { EntitlementDetailsHeader } from '~features/entitlements/components/EntitlementDetailsHeader';
import {
    AddEntitlementsFormValues,
    EntitlementsForm,
} from '~features/modal/entitlement/EntitlementsForm';
import { OrganizationDetailsHeader } from '~features/organizations/components/OrganizationDetailsHeader';
import { PageShell, PageShellNavItem } from '~shared/components/page-shell';
import { useNotifyParentChildModal } from '~shared/hooks/useNotifyParentChildModal';

import { StandaloneShellProvider } from './StandaloneShellContext';

const NAV_ITEMS: PageShellNavItem[] = [
  { path: PATHS.organizations.root, label: 'Organizations' },
  { path: PATHS.entitlements.root, label: 'Entitlements' },
];

export function MainLayout() {
    const [isAddOpen, setIsAddOpen] = useState(false);
    const navItems = useMemo(() => NAV_ITEMS, []);

    const entitlementMatch = useMatch(PATHS.entitlements.detailMatch);
    const organizationMatch = useMatch(PATHS.organizations.detailMatch);

    useNotifyParentChildModal(isAddOpen);

    return (
        <StandaloneShellProvider>
            <PageShell>
                {entitlementMatch?.params.entitlementId ? (
                    <EntitlementDetailsHeader
                        entitlementId={entitlementMatch.params.entitlementId}
                        backUrl={PATHS.entitlements.root}
                    />
                ) : organizationMatch?.params.organizationId ? (
                    <OrganizationDetailsHeader
                        organizationId={organizationMatch.params.organizationId}
                        backUrl={PATHS.organizations.root}
                    />
                ) : (
                    <PageShell.Header
                        items={navItems}
                        actions={
                            <Button
                                type="primary"
                                onClick={() => setIsAddOpen(true)}
                                testId="add-organization-button"
                            >
                                Add organization
                            </Button>
                        }
                    />
                )}
                <PageShell.Content>
                    <Outlet />
                </PageShell.Content>
            </PageShell>
            <EntitlementsForm
                isOpen={isAddOpen}
                onClose={() => setIsAddOpen(false)}
                onSubmit={(values: AddEntitlementsFormValues) => {
                    console.log('[entitlements] add entitlement submitted', values);
                }}
            />
        </StandaloneShellProvider>
    );
}
