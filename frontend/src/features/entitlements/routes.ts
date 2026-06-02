import { redirect, RouteObject } from "react-router-dom";

import { lazyComponent } from "~shared/utils/lazyComponent";

export const entitlementsRoutes: RouteObject = {
  path: "entitlements",
  children: [
    {
      index: true,
      lazy: lazyComponent(
        () => import("~features/entitlements/list/EntitlementsGrid"),
        "EntitlementsGrid",
      ),
    },
    {
      path: ":entitlementId",
      lazy: lazyComponent(
        () => import("~features/entitlements/details/DetailsContent"),
        "EntitlementDetailsContent",
      ),
      children: [
        { index: true, loader: () => redirect("general") },
        {
          path: "general",
          lazy: lazyComponent(
            () => import("~features/entitlements/details/general/General"),
            "EntitlementsGeneralDetails",
          ),
        },
      ],
    },
  ],
};
