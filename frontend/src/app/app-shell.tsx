import { Outlet, useMatches } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import { Button } from '@swo/design-system/button';
import { AppNav, AppNavItem } from '~shared/components/app-nav';
import {
    AddOrganizationFormValues,
    AddOrganizationModal,
} from '~features/organizations/components/add-organization-modal';
import { ExtensionsProvider } from '~shared/providers/extensions-provider';
import { i18n } from '~i18n/translations';
import '~styles/global.scss';

const NAV_ITEMS: AppNavItem[] = [
    { path: '/entitlements', label: 'Entitlements' },
    { path: '/organizations', label: 'Organizations' },
];

/**
 * Application shell layout: providers, top-level `AppNav`, "Add organization"
 * modal, and the parent-frame `postMessage` bridge used when running embedded
 * inside an iframe. Renders the active route via `<Outlet />`.
 *
 * Routes can opt out of the parent `AppNav` by exporting
 * `handle = { hideAppNav: true }` from their route module.
 */
export function AppShell() {
    const [isAddOpen, setIsAddOpen] = useState(false);

    useEffect(() => {
        if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: 'child-modal', isOpen: isAddOpen }, '*');
        }
        // eslint-disable-next-line no-console
        console.log('[entitlements] modal state ->', isAddOpen);
    }, [isAddOpen]);

    const navItems = useMemo(() => NAV_ITEMS, []);

    const matches = useMatches();
    const hideAppNav = matches.some(
        (m) => (m.handle as { hideAppNav?: boolean } | undefined)?.hideAppNav,
    );

    return (
        <ExtensionsProvider i18n={i18n}>
            <div className="entitlements-app">
                {hideAppNav ? (
                    <Outlet />
                ) : (
                    <AppNav
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
                    >
                        <Outlet />
                    </AppNav>
                )}
                <AddOrganizationModal
                    isOpen={isAddOpen}
                    onClose={() => setIsAddOpen(false)}
                    onSubmit={(values: AddOrganizationFormValues) => {
                        // eslint-disable-next-line no-console
                        console.log('[entitlements] add organization submitted', values);
                    }}
                />
            </div>
        </ExtensionsProvider>
    );
}
