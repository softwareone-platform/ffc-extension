import { Suspense, lazy, useEffect } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { OrganizationDetails } from "./Details/Organization.Details";

// import { app } from "@/config";

// TODO: Out of scope for v4. Back in v5
// const Analytics = lazy(() => import('@/Modules/Analytics').then(m => ({ default: m.Analytics })));
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
  //   const user = useUserData();
  //   const role = user.accountType!;
  //   const isAllowed = !!user.modules?.includes('billing');
  //   const { handleError } = useErrorHandler();

  //   useEffect(() => {
  //     if (isAllowed) {
  //       return;
  //     }
  //     handleError('403');
  //   }, [handleError, isAllowed]);

  return (
    <Suspense>
      <Routes>
        <Route
          element={
            <div data-testid={"billing"}>
              <Suspense fallback={<></>}>
                <Outlet></Outlet>
              </Suspense>
            </div>
          }
        >
          {/* <Route path={"*"} index element={<OrganizationsGrid />} /> */}
          <Route index element={<OrganizationsGrid />} />
          <Route path=":organizationId" element={<Details />} />
          {/* <Route path=":organizationId/details" element={<Details />} /> */}
        </Route>
      </Routes>
    </Suspense>
  );
}
