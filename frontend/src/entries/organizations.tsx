import { createRoot } from "react-dom/client";

import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";

import { OrganizationDataSources } from "~features/organizations/details/data-sources/DataSources";
import { OrganizationDetailsLayout } from "~features/organizations/details/DetailsLayout";
import { OrganizationGeneralDetails } from "~features/organizations/details/general/General";
import { OrganizationUsers } from "~features/organizations/details/users/Users";
import { OrganizationsGrid } from "~features/organizations/list/OrganizationsGrid";
import { i18n } from "~i18n/translations";
import { ExtensionsProvider } from "~shared/providers/ExtensionsProvider";

import "~styles/global.scss";

import { setup } from "@mpt-extension/sdk";

/**
 * Standalone "Organizations" widget bundle. Mounted by the host as a
 * top-level micro-frontend at its own root, so it owns its providers and
 * router. Reuses the same feature components as the main router.
 */
setup((element: Element) => {
  const root = createRoot(element);
  root.render(
    <ExtensionsProvider i18n={i18n}>
      <BrowserRouter>
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
      </BrowserRouter>
    </ExtensionsProvider>,
  );
});
