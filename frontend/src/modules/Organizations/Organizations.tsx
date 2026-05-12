import { lazy, Suspense } from 'react';
import { Outlet, Route, Routes } from 'react-router-dom';
const OrganizationsGrid = lazy(() =>
  import("./Grid/Organizations.Grid").then((m) => ({
    default: m.OrganizationsGrid,
  })),
);
const Details = lazy(() =>
  import("./Details/Organization.Details").then((m) => ({
    default: m.OrganizationDetails,
  })),
);

export function Organizations() {
  return (
    <Suspense>
      <Routes>
        <Route
          element={
            <div data-testid={"ffc-organizations"}>
              <Suspense fallback={<></>}>
                <Outlet></Outlet>
              </Suspense>
            </div>
          }
        >
          <Route index element={<OrganizationsGrid />} />
          <Route path=":organizationId/*" element={<Details />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
