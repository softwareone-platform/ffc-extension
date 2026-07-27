import { lazy } from "react";

import { Navigate, Route, Routes } from "react-router-dom";

import { SEGMENTS } from "~features/entitlements/paths";
import { RouteGuard } from "~shared/components/RouteGuard";

const EntitlementsGrid = lazy(() =>
  import("~features/entitlements/list/EntitlementsGrid").then((m) => ({
    default: m.EntitlementsGrid,
  })),
);
const EntitlementsGeneralDetails = lazy(() =>
  import("~features/entitlements/details/general/General").then((m) => ({
    default: m.EntitlementsGeneralDetails,
  })),
);
const EntitlementDetailsContent = lazy(() =>
  import("~features/entitlements/details/DetailsContent").then((m) => ({
    default: m.EntitlementDetailsContent,
  })),
);

const allowedRoles = ["admin", "operations", "affiliate"] as const;

export function Entitlements() {
  return (
    <RouteGuard allowedRoles={allowedRoles}>
      <Routes>
        <Route index element={<EntitlementsGrid />} />
        <Route path={SEGMENTS.idParam} element={<EntitlementDetailsContent />}>
          <Route index element={<Navigate to={SEGMENTS.general} replace />} />
          <Route path={SEGMENTS.general} element={<EntitlementsGeneralDetails />} />
        </Route>
      </Routes>
    </RouteGuard>
  );
}
