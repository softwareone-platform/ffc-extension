import { redirect, RouteObject } from "react-router-dom";

import { SEGMENTS } from "~features/organizations/paths";
import { lazyComponent } from "~shared/utils/lazyComponent";

export const organizationsRoutes: RouteObject = {
  path: SEGMENTS.root,
  children: [
    {
      index: true,
      lazy: lazyComponent(
        () => import("~features/organizations/list/OrganizationsGrid"),
        "OrganizationsGrid",
      ),
    },
    {
      path: SEGMENTS.idParam,
      lazy: lazyComponent(
        () => import("~features/organizations/details/DetailsContent"),
        "OrganizationDetailsContent",
      ),
      children: [
        { index: true, loader: () => redirect(SEGMENTS.general) },
        {
          path: SEGMENTS.general,
          lazy: lazyComponent(
            () => import("~features/organizations/details/general/General"),
            "OrganizationGeneralDetails",
          ),
        },
        {
          path: SEGMENTS.dataSources,
          lazy: lazyComponent(
            () => import("~features/organizations/details/data-sources/DataSources"),
            "OrganizationDataSources",
          ),
        },
        {
          path: SEGMENTS.users,
          lazy: lazyComponent(
            () => import("~features/organizations/details/users/Users"),
            "OrganizationUsers",
          ),
        },
      ],
    },
  ],
};
