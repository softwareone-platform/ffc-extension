import { lazy } from "react";

import { Navigate, Route, Routes } from "react-router-dom";

import { DetailsLayout } from "~app/layouts";
import { PARAMS, SEGMENTS } from "~features/entitlements/paths";
import { RouteGuard } from "~shared/components/RouteGuard";

import { EntitlementDetailsHeader } from "./components/EntitlementDetailsHeader";

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

export function Entitlements({ isStandalone = true }: { isStandalone?: boolean }) {
  return (
    <RouteGuard allowedRoles={allowedRoles}>
      <Routes>
        <Route index element={<EntitlementsGrid />} />
        <Route
          path={SEGMENTS.idParam}
          element={
            isStandalone ? (
              <EntitlementDetailsContent />
            ) : (
              <DetailsLayout
                paramKey={PARAMS.entitlementId}
                renderHeader={(id, backUrl) => (
                  <EntitlementDetailsHeader entitlementId={id} backUrl={backUrl} />
                )}
              >
                <EntitlementDetailsContent />
              </DetailsLayout>
            )
          }
        >
          <Route index element={<Navigate to={SEGMENTS.general} replace />} />
          <Route path={SEGMENTS.general} element={<EntitlementsGeneralDetails />} />
        </Route>
      </Routes>
    </RouteGuard>
  );
}
