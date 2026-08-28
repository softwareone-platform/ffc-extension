import { lazy, Suspense } from "react";

import { Navigate, Route, Routes } from "react-router-dom";

import { FEATURE_FLAGS } from "~app/featureFlags";
import { PATHS } from "~app/paths";
import { SEGMENTS as DASHBOARD_SEGMENTS } from "~features/dashboard/paths";
import { useUserRole } from "~shared/hooks/useUserRole";

const MainLayout = lazy(() => import("~app/layouts").then((m) => ({ default: m.MainLayout })));
const Dashboard = lazy(() =>
  import("~features/dashboard/Dashboard").then((m) => ({ default: m.Dashboard })),
);
const AdoptionTab = lazy(() =>
  import("~features/dashboard/tabs/AdoptionTab").then((m) => ({ default: m.AdoptionTab })),
);
const ConsumptionTab = lazy(() =>
  import("~features/dashboard/tabs/ConsumptionTab").then((m) => ({ default: m.ConsumptionTab })),
);
const HealthTab = lazy(() =>
  import("~features/dashboard/tabs/HealthTab").then((m) => ({ default: m.HealthTab })),
);
const MaturityTab = lazy(() =>
  import("~features/dashboard/tabs/MaturityTab").then((m) => ({ default: m.MaturityTab })),
);
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
        {FEATURE_FLAGS.dashboard && (
          <Route path={DASHBOARD_SEGMENTS.root} element={<Dashboard />}>
            <Route index element={<Navigate to={DASHBOARD_SEGMENTS.consumption} replace />} />
            <Route path={DASHBOARD_SEGMENTS.adoption} element={<AdoptionTab />} />
            <Route path={DASHBOARD_SEGMENTS.consumption} element={<ConsumptionTab />} />
            <Route path={DASHBOARD_SEGMENTS.health} element={<HealthTab />} />
            <Route path={DASHBOARD_SEGMENTS.maturity} element={<MaturityTab />} />
          </Route>
        )}
        <Route path={"organizations/*"} element={<Organizations />} />
        <Route path={"entitlements/*"} element={<Entitlements />} />
      </Route>
    </Routes>
  );
}
