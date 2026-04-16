import { Suspense, lazy, useEffect } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

// import { app } from "@/config";

// TODO: Out of scope for v4. Back in v5
// const Analytics = lazy(() => import('@/Modules/Analytics').then(m => ({ default: m.Analytics })));
const OrganizationsGrid = lazy(() =>
  import("./Grid/Organizations.Grid").then((m) => ({ default: m.OrganizationsGrid })),
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
          {/* TODO: Out of scope for v4. Back in v5 */}
          {/* <Route path={'analytics/*'} element={<Analytics />} /> */}
          {/* <Route path={"overrides/*"} element={<Override />} />
          <Route path={"custom-ledgers/*"} element={<CustomLedger />} />
          <Route path={"invoices/*"} element={<Invoice />} />
          <Route path={"credit-memos/*"} element={<CreditMemo />} />
          <Route path={"journals/*"} element={<Journal />} />
          <Route path={"ledgers/*"} element={<Ledger />} />
          <Route path={"statements/*"} element={<Statement />} />
          <Route
            index
            element={
              <Navigate to={role === "Client" ? "statements" : "journals"} />
            }
          /> */}

          <Route
            path={"*"}
            element={<OrganizationsGrid />
            }
          />
        </Route>
      </Routes>
    </Suspense>
  );
}
