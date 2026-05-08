import { createRoot } from 'react-dom/client';
import { HashRouter, Outlet, Route, Routes } from 'react-router-dom';
import { setup } from '@mpt-extension/sdk';
import { ExtensionsProvider } from '~shared/providers/extensions-provider';
import { i18n } from '~i18n/translations';
import { OrganizationsGrid } from '~features/organizations/list/organizations-grid';
import { OrganizationDetailsLayout } from '~features/organizations/details/details-layout';
import { OrganizationGeneralDetails } from '~features/organizations/details/general';
import { OrganizationDataSources } from '~features/organizations/details/data-sources/data-sources';
import { OrganizationUsers } from '~features/organizations/details/users/users';
import '~styles/global.scss';

/**
 * Standalone "Organizations" widget bundle. Mounted by the host as a
 * top-level micro-frontend at its own root, so it owns its providers and
 * router. Reuses the same feature components as the main router.
 */
setup((element: Element) => {
    const root = createRoot(element);
    root.render(
        <ExtensionsProvider i18n={i18n}>
            <HashRouter>
                <Routes>
                    <Route element={<Outlet />}>
                        <Route index element={<OrganizationsGrid />} />
                        <Route path=":organizationId" element={<OrganizationDetailsLayout />}>
                            <Route index element={<OrganizationGeneralDetails />} />
                            <Route path="general" element={<OrganizationGeneralDetails />} />
                            <Route path="data-sources" element={<OrganizationDataSources />} />
                            <Route path="users" element={<OrganizationUsers />} />
                        </Route>
                    </Route>
                </Routes>
            </HashRouter>
        </ExtensionsProvider>,
    );
});
