import { lazy, Suspense, useContext } from "react";

import { Navigate, Route, Routes } from "react-router-dom";

import { PATHS } from "~app/paths";
import { UserContext } from "~shared/providers/UserContext";

const MainLayout = lazy(() => import("~app/layouts").then((m) => ({ default: m.MainLayout })));
const Organizations = lazy(() =>
  import("~features/organizations/Organizations").then((m) => ({ default: m.Organizations })),
);
const Entitlements = lazy(() =>
  import("~features/entitlements/Entitlements").then((m) => ({ default: m.Entitlements })),
);

export function App() {
  const user = useContext(UserContext);
  const role = user?.account.type;

  return (
    <Routes>
      <Route
        index
        element={
          <Navigate
            to={role === "affiliate" ? PATHS.entitlements.root : PATHS.organizations.root}
          />
        }
      />
      <Route
        element={
          <div data-testid={"ffc-extension"}>
            <Suspense fallback={<></>}>
              <MainLayout />
            </Suspense>
          </div>
        }
      >
        <Route path={"organizations/*"} element={<Organizations />} />
        <Route path={"entitlements/*"} element={<Entitlements />} />
      </Route>
    </Routes>
  );
}
