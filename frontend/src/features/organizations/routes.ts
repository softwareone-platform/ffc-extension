import { redirect, RouteObject } from "react-router-dom";

import { lazyComponent } from "~shared/utils/lazyComponent";

export const organizationsRoutes: RouteObject = {
  path: "organizations",
  children: [
    {
      index: true,
      lazy: lazyComponent(
        () => import("~features/organizations/list/OrganizationsGrid"),
        "OrganizationsGrid",
      ),
    },
    {
      path: ":organizationId",
      lazy: lazyComponent(
        () => import("~features/organizations/details/DetailsLayout"),
        "OrganizationDetailsLayout",
      ),
      children: [
        { index: true, loader: () => redirect("general") },
        {
          path: "general",
          lazy: lazyComponent(
            () => import("~features/organizations/details/general/General"),
            "OrganizationGeneralDetails",
          ),
        },
        {
          path: "data-sources",
          lazy: lazyComponent(
            () => import("~features/organizations/details/data-sources/DataSources"),
            "OrganizationDataSources",
          ),
        },
        {
          path: "users",
          lazy: lazyComponent(
            () => import("~features/organizations/details/users/Users"),
            "OrganizationUsers",
          ),
        },
      ],
    },
  ],
};
