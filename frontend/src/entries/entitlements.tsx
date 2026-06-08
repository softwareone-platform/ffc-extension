import { createRoot } from "react-dom/client";

import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";

import { DetailsLayout } from "~app/layouts";
import { PARAMS, SEGMENTS } from "~app/paths";
import { EntitlementDetailsHeader } from "~features/entitlements/components/EntitlementDetailsHeader";
import { EntitlementDetailsContent } from "~features/entitlements/details/DetailsContent";
import { EntitlementsGeneralDetails } from "~features/entitlements/details/general/General";
import { EntitlementsGrid } from "~features/entitlements/list/EntitlementsGrid";
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
            <Route index element={<EntitlementsGrid />} />
            <Route
              path={SEGMENTS.entitlementIdParam}
              element={
                <DetailsLayout
                  paramKey={PARAMS.entitlementId}
                  renderHeader={(id, backUrl) => (
                    <EntitlementDetailsHeader entitlementId={id} backUrl={backUrl} />
                  )}
                >
                  <EntitlementDetailsContent />
                </DetailsLayout>
              }
            >
              <Route index element={<Navigate to={SEGMENTS.general} replace />} />
              <Route path={SEGMENTS.general} element={<EntitlementsGeneralDetails />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ExtensionsProvider>,
  );
});
