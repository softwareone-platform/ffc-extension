import { lazy, Suspense } from "react";

import { Navigate, Route, Routes } from "react-router-dom";

import { PATHS } from "~app/paths";
import { useUserRole } from "~shared/hooks/useUserRole";

const MainLayout = lazy(() => import("~app/layouts").then((m) => ({ default: m.MainLayout })));
const Organizations = lazy(() =>
  import("~features/organizations/Organizations").then((m) => ({ default: m.Organizations })),
);
const Entitlements = lazy(() =>
  import("~features/entitlements/Entitlements").then((m) => ({ default: m.Entitlements })),
);

export function App() {
  const { role } = useUserRole();

  return (
    <Routes>
      <Route
        index
        element={
          // `replace` is required: the plug runs in an iframe whose history entries join the
          // portal's session history. A push here leaves `/` behind the landing page, so the
          // browser Back button lands on `/`, which redirects forward again and traps the user
          // inside the extension instead of returning to the previous portal page.
          <Navigate
            to={role === "affiliate" ? PATHS.entitlements.root : PATHS.organizations.root}
            replace
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
