import React, { useEffect, useRef, useState } from 'react';
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
    const navRef = useRef<HTMLElement>(null);
    const [navOffset, setNavOffset] = useState(0);
    const [navHeight, setNavHeight] = useState(0);
    const [isAddOpen, setIsAddOpen] = useState(false);

    useEffect(() => {
        if (navRef.current) {
            setNavHeight(navRef.current.offsetHeight);
        }
    }, []);

    useEffect(() => {
        const handleMessage = (event: MessageEvent) => {
            const data = event.data;
            if (!data || data.type !== 'parent-scroll') return;

            const {
                iframeTop,
                iframeHeight,
                viewportHeight,
                headerBottom = 0,
            } = data as {
                iframeTop: number;
                iframeHeight: number;
                viewportHeight: number;
                headerBottom?: number;
            };

            const desiredTopInsideIframe = Math.max(0, headerBottom - iframeTop);
            const navH = navRef.current?.offsetHeight ?? navHeight;
            const wrapperH =
                (navRef.current?.parentElement as HTMLElement | null)?.offsetHeight ??
                iframeHeight;
            const maxOffset = Math.max(0, wrapperH - navH);
            const visibleBottomCap = Math.max(
                0,
                Math.min(iframeHeight, viewportHeight - iframeTop) - navH
            );
            const target = Math.min(desiredTopInsideIframe, maxOffset, visibleBottomCap);
            setNavOffset(target > 0 ? target : 0);
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [navHeight]);

    return (
        <>
            <nav
                ref={navRef as React.RefObject<HTMLElement>}
                id="myNav"
                role="tablist"
                style={{ ['--nav-offset' as never]: `${navOffset}px` }}
            >
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
            {/* Spacer to reserve nav height since nav is absolutely positioned */}
            <div
                className="entitlements-app__nav-spacer"
                style={{ height: navHeight }}
                aria-hidden="true"
            />
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

