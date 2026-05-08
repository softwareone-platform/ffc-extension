import { useEffect, useMemo, useState } from 'react';

import { Outlet } from 'react-router-dom';

import { Button } from '@swo/design-system/button';

import {
    AddOrganizationFormValues,
    AddOrganizationModal,
} from '~features/organizations/components/add-organization-modal';
import { PageShell, PageShellNavItem } from '~shared/components/page-shell';

const NAV_ITEMS: PageShellNavItem[] = [
    { path: '/entitlements', label: 'Entitlements' },
    { path: '/organizations', label: 'Organizations' },
];

/**
 * App-wide layout: renders the shared `PageShell` with section tabs
 * (Entitlements, Organizations) plus the "Add organization" action and modal.
 *
 * Used as the route-tree layout for top-level list pages. Detail routes
 * (e.g. organization details) supply their own `PageShell` and bypass this
 * layout so the user only ever sees a single header bar.
 *
 * NOTE: feature-specific layouts (like `OrganizationDetailsLayout`) live
 * inside their feature folder, not here. This folder is for app-wide shells.
 */
export function MainLayout() {
    const [isAddOpen, setIsAddOpen] = useState(false);

    useEffect(() => {
        if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: 'child-modal', isOpen: isAddOpen }, '*');
        }
        console.log('[entitlements] modal state ->', isAddOpen);
    }, [isAddOpen]);

    const navItems = useMemo(() => NAV_ITEMS, []);

    return (
        <>
            <PageShell>
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
