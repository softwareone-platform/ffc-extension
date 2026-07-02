import { createBrowserRouter, redirect } from "react-router-dom";

import { mountStandaloneEntry } from "~app/bootstrap/mountStandaloneEntry";
import { PATHS } from "~app/paths";
import { entitlementsRoutes } from "~features/entitlements/routes";
import { organizationsRoutes } from "~features/organizations/routes";
import { lazyComponent } from "~shared/utils/lazyComponent";

const router = createBrowserRouter([
  {
    path: PATHS.root,
    children: [
      { index: true, loader: () => redirect(PATHS.organizations.root) },
      {
        lazy: lazyComponent(() => import("~app/layouts"), "MainLayout"),
        children: [entitlementsRoutes, organizationsRoutes],
      },
    ],
  },
]);

mountStandaloneEntry(router);
