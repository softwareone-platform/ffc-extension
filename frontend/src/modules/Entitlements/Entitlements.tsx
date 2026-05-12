import { lazy, Suspense } from 'react';
import { Outlet, Route, Routes } from 'react-router-dom';
// import { EntitlementsGrid } from './Grid/Entitlements.Grid';
const EntitlementsGrid = lazy(() =>
  import("./Grid/Entitlements.Grid").then((m) => ({
    default: m.EntitlementsGrid,
  })),
);
const Details = lazy(() =>
  import("./Details/Entitlement.Details").then((m) => ({
    default: m.EntitlementDetails,
  })),
);

export function Entitlements() {
  return (
    <Suspense>
      <Routes>
        <Route
          element={
            <div data-testid={"ffc-entitlements"}>
              <Suspense fallback={<></>}>
                <Outlet></Outlet>
              </Suspense>
            </div>
          }
        >
          <Route index element={<EntitlementsGrid />} />
          <Route path=":entitlementId/*" element={<Details />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
