import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
    HashRouter,
    NavLink,
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
import './entitlements.scss';

type RouteDef = {
    path: string;
    label: string;
    element: React.ReactNode;
};

const routes: RouteDef[] = [
    { path: '/entitlements', label: 'Entitlements', element: <EntitlementsPage /> },
    { path: '/organizations', label: 'Organizations', element: <OrganizationsPage /> },
];

const DEFAULT_PATH = routes[0].path;

const StickyNav: React.FC = () => {
    const [isAddOpen, setIsAddOpen] = useState(false);

    return (
        <>
            <nav id="myNav" role="tablist">
                <div className="entitlements-app__tabs">
                    {routes.map((route) => (
                        <NavLink
                            key={route.path}
                            to={route.path}
                            role="tab"
                            className={({ isActive }) =>
                                `entitlements-app__tab${isActive ? ' is-active' : ''}`
                            }
                        >
                            {route.label}
                        </NavLink>
                    ))}
                </div>
                <div className="entitlements-app__nav-actions">
                    <Button
                        type="primary"
                        onClick={() => setIsAddOpen(true)}
                        testId="add-organization-button"
                    >
                        Add organization
                    </Button>
                </div>
            </nav>
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
            <StickyNav />
            <div role="tabpanel" className="entitlements-app__tabpanel">
                <Routes>
                    {routes.map((route) => (
                        <Route key={route.path} path={route.path} element={route.element} />
                    ))}
                    <Route path="*" element={<Navigate to={DEFAULT_PATH} replace />} />
                </Routes>
            </div>
        </div>
    </HashRouter>
);

setup((element: Element) => {
    const root = createRoot(element);
    root.render(<App />);
});

