import { redirect, RouteObject } from "react-router-dom";

import { SEGMENTS } from "~app/paths";
import { lazyComponent } from "~shared/utils/lazyComponent";

export const entitlementsRoutes: RouteObject = {
  path: SEGMENTS.entitlements,
  children: [
    {
      index: true,
      lazy: lazyComponent(
        () => import("~features/entitlements/list/EntitlementsGrid"),
        "EntitlementsGrid",
      ),
    },
    {
      path: SEGMENTS.entitlementIdParam,
      lazy: lazyComponent(
        () => import("~features/entitlements/details/DetailsContent"),
        "EntitlementDetailsContent",
      ),
      children: [
        { index: true, loader: () => redirect(SEGMENTS.general) },
        {
          path: SEGMENTS.general,
          lazy: lazyComponent(
            () => import("~features/entitlements/details/general/General"),
            "EntitlementsGeneralDetails",
          ),
        },
      ],
    },
  ],
};
