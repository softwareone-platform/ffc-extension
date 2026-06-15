import { createBrowserRouter, redirect } from 'react-router-dom';

import { entitlementsRoutes } from "~features/entitlements/routes";
import { organizationsRoutes } from "~features/organizations/routes";
import { lazyComponent } from "~shared/utils/lazyComponent";

/**
 * Application route tree. URL → component wiring lives here; each feature
 * owns its own route partial under `features/<name>/routes.ts`.
 */
export const router = createBrowserRouter([
  {
    path: "/",
    lazy: lazyComponent(() => import("~app/AppShell"), "AppShell"),
    children: [
      { index: true, loader: () => redirect("/entitlements") },
      {
        // Top-level layout: renders the shared PageShell (Entitlements /
        // Organizations tabs + "Add organization" action) for list pages.
        lazy: lazyComponent(() => import("~app/layouts"), "MainLayout"),
        children: [entitlementsRoutes, organizationsRoutes],
      },
    ],
  },
]);
