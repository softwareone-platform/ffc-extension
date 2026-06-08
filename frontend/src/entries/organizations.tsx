import { createRoot } from "react-dom/client";

import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";

import { DetailsLayout } from "~app/layouts";
import { PARAMS, SEGMENTS } from "~app/paths";
import { OrganizationDetailsHeader } from "~features/organizations/components/OrganizationDetailsHeader";
import { OrganizationDataSources } from "~features/organizations/details/data-sources/DataSources";
import { OrganizationDetailsContent } from "~features/organizations/details/DetailsContent";
import { OrganizationGeneralDetails } from "~features/organizations/details/general/General";
import { OrganizationUsers } from "~features/organizations/details/users/Users";
import { OrganizationsGrid } from "~features/organizations/list/OrganizationsGrid";
import { i18n } from "~i18n/translations";
import { ExtensionsProvider } from "~shared/providers/ExtensionsProvider";

import "~styles/global.scss";

import { setup } from "@mpt-extension/sdk";

setup((element: Element) => {
  const root = createRoot(element);
  root.render(
    <ExtensionsProvider i18n={i18n}>
      <BrowserRouter>
        <Routes>
          <Route element={<Outlet />}>
            <Route index element={<OrganizationsGrid />} />
            <Route
              path={SEGMENTS.organizationIdParam}
              element={
                <DetailsLayout
                  paramKey={PARAMS.organizationId}
                  renderHeader={(id, backUrl) => (
                    <OrganizationDetailsHeader organizationId={id} backUrl={backUrl} />
                  )}
                >
                  <OrganizationDetailsContent />
                </DetailsLayout>
              }
            >
              <Route index element={<OrganizationGeneralDetails />} />
              <Route path={SEGMENTS.general} element={<OrganizationGeneralDetails />} />
              <Route path={SEGMENTS.dataSources} element={<OrganizationDataSources />} />
              <Route path={SEGMENTS.users} element={<OrganizationUsers />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ExtensionsProvider>,
  );
});
