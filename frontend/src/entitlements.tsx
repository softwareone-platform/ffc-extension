import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
    HashRouter,
    Navigate,
    Route,
    Routes,
} from 'react-router-dom';
import { setup } from '@mpt-extension/sdk';
import { Button } from '@swo/design-system/button';
import EntitlementsPage from './pages/EntitlementsPage';
import OrganizationsPage from './pages/OrganizationsPage';
import {
    AddOrganizationFormValues,
    AddOrganizationModal,
} from './components/AddOrganizationModal';
import { AppNav, AppNavItem } from './shared/components/AppNav';
import './entitlements.scss';

type RouteDef = AppNavItem & {
    element: React.ReactNode;
};

const routes: RouteDef[] = [
    { path: '/entitlements', label: 'Entitlements', element: <EntitlementsPage /> },
    { path: '/organizations', label: 'Organizations', element: <OrganizationsPage /> },
];

const DEFAULT_PATH = routes[0].path;

const AppShell: React.FC = () => {
    const [isAddOpen, setIsAddOpen] = useState(false);

    useEffect(() => {
        if (window.parent && window.parent !== window) {
            window.parent.postMessage(
                { type: 'child-modal', isOpen: isAddOpen },
                '*'
            );
        }
        // eslint-disable-next-line no-console
        console.log('[entitlements] modal state ->', isAddOpen);
    }, [isAddOpen]);

    const navItems = useMemo<AppNavItem[]>(
        () => routes.map(({ path, label }) => ({ path, label })),
        []
    );

    return (
        <>
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
                <Routes>
                    {routes.map((route) => (
                        <Route key={route.path} path={route.path} element={route.element} />
                    ))}
                    <Route path="*" element={<Navigate to={DEFAULT_PATH} replace />} />
                </Routes>
            </AppNav>
            <AddOrganizationModal
                isOpen={isAddOpen}
                onClose={() => setIsAddOpen(false)}
                onSubmit={(values: AddOrganizationFormValues) => {
                    // Sample submit handler — replace with real API call.
                    // eslint-disable-next-line no-console
                    console.log('[entitlements] add organization submitted', values);
                }}
            />
        </>
    );
};

const App: React.FC = () => (
    <HashRouter>
        <div className="entitlements-app">
            <AppShell />
        </div>
    </HashRouter>
);

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<App />);
});
