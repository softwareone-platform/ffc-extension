import { createRoot } from "react-dom/client";

import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";

import { EntitlementsDetailsLayout } from "~features/entitlements/details/DetailsLayout";
import { EntitlementsGeneralDetails } from "~features/entitlements/details/general/General";
import { EntitlementsGrid } from "~features/entitlements/list/EntitlementsGrid";
import { i18n } from "~i18n/translations";
import { ExtensionsProvider } from "~shared/providers/ExtensionsProvider";

import "~styles/global.scss";

import { setup } from "@mpt-extension/sdk";

/**
 * Standalone "Entitlements" widget bundle. Mounted by the host as a
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
            <Route index element={<EntitlementsGrid />} />
            <Route path=":entitlementId" element={<EntitlementsDetailsLayout />}>
              <Route index element={<Navigate to="general" replace />} />
              <Route path="general" element={<EntitlementsGeneralDetails />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ExtensionsProvider>,
  );
});
