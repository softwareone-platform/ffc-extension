import { lazy } from "react";

import { Route, Routes } from "react-router-dom";

import { SEGMENTS } from "~features/organizations/paths";
import { RouteGuard } from "~shared/components/RouteGuard";

const OrganizationsGrid = lazy(() =>
  import("~features/organizations/list/OrganizationsGrid").then((m) => ({
    default: m.OrganizationsGrid,
  })),
);
const OrganizationDetailsContent = lazy(() =>
  import("~features/organizations/details/DetailsContent").then((m) => ({
    default: m.OrganizationDetailsContent,
  })),
);
const OrganizationGeneralDetails = lazy(() =>
  import("~features/organizations/details/general/General").then((m) => ({
    default: m.OrganizationGeneralDetails,
  })),
);
const OrganizationDataSources = lazy(() =>
  import("~features/organizations/details/data-sources/DataSources").then((m) => ({
    default: m.OrganizationDataSources,
  })),
);
const OrganizationUsers = lazy(() =>
  import("~features/organizations/details/users/Users").then((m) => ({
    default: m.OrganizationUsers,
  })),
);
const OrganizationEventsDetails = lazy(() =>
  import("~features/organizations/details/events/Events").then((m) => ({
    default: m.OrganizationEventsDetails,
  })),
);

const allowedRoles = ["admin", "operations"] as const;

export function Organizations() {
  return (
    <RouteGuard allowedRoles={allowedRoles}>
      <Routes>
        <Route index element={<OrganizationsGrid />} />
        <Route path={SEGMENTS.idParam} element={<OrganizationDetailsContent />}>
          <Route index element={<OrganizationGeneralDetails />} />
          <Route path={SEGMENTS.general} element={<OrganizationGeneralDetails />} />
          <Route path={SEGMENTS.dataSources} element={<OrganizationDataSources />} />
          <Route path={SEGMENTS.users} element={<OrganizationUsers />} />
          <Route path={SEGMENTS.events} element={<OrganizationEventsDetails />} />
        </Route>
      </Routes>
    </RouteGuard>
  );
}
