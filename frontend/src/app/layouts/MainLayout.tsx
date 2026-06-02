import { useEffect, useMemo, useState } from 'react';

import { Outlet, useMatch } from 'react-router-dom';

import { Button } from '@swo/design-system/button';

import { EntitlementDetailsHeader } from '~features/entitlements/components/EntitlementDetailsHeader';
import {
    AddOrganizationFormValues,
    AddOrganizationModal,
} from '~features/organizations/components/AddOrganizationModal';
import { OrganizationDetailsHeader } from '~features/organizations/components/OrganizationDetailsHeader';
import { PageShell, PageShellNavItem } from '~shared/components/page-shell';

const NAV_ITEMS: PageShellNavItem[] = [
  { path: '/organizations', label: 'Organizations' },
  { path: '/entitlements', label: 'Entitlements' },
];

export function MainLayout() {
    const [isAddOpen, setIsAddOpen] = useState(false);
    const navItems = useMemo(() => NAV_ITEMS, []);

    const entitlementMatch = useMatch('/entitlements/:entitlementId/*');
    const organizationMatch = useMatch('/organizations/:organizationId/*');

    useEffect(() => {
        if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: 'child-modal', isOpen: isAddOpen }, '*');
        }
    }, [isAddOpen]);

    return (
        <>
            <PageShell>
                {entitlementMatch?.params.entitlementId ? (
                    <EntitlementDetailsHeader
                        entitlementId={entitlementMatch.params.entitlementId}
                        backUrl="/entitlements"
                    />
                ) : organizationMatch?.params.organizationId ? (
                    <OrganizationDetailsHeader
                        organizationId={organizationMatch.params.organizationId}
                        backUrl="/organizations"
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
            <AddOrganizationModal
                isOpen={isAddOpen}
                onClose={() => setIsAddOpen(false)}
                onSubmit={(values: AddOrganizationFormValues) => {
                    console.log('[entitlements] add organization submitted', values);
                }}
            />
        </>
    );
}
