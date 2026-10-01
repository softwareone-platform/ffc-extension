import { ReactElement } from "react";

import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

type Options = {
  initialUrl: string;
  routePath: string;
};

type EntityRouteOptions = {
  id?: string;
  initialUrl?: string;
  routePath?: string;
};

export function renderWithRouter(ui: ReactElement, { initialUrl, routePath }: Options) {
  return render(
    <MemoryRouter initialEntries={[initialUrl]}>
      <Routes>
        <Route path={routePath} element={ui} />
      </Routes>
    </MemoryRouter>,
  );
}

export function renderWithEntitlementRoute(
  ui: ReactElement,
  { id = "ent-1", initialUrl, routePath = "/entitlements/:entitlementId" }: EntityRouteOptions = {},
) {
  return renderWithRouter(ui, {
    initialUrl: initialUrl ?? `/entitlements/${id}`,
    routePath,
  });
}

export function renderWithOrganizationRoute(
  ui: ReactElement,
  {
    id = "org-1",
    initialUrl,
    routePath = "/organizations/:organizationId",
  }: EntityRouteOptions = {},
) {
  return renderWithRouter(ui, {
    initialUrl: initialUrl ?? `/organizations/${id}`,
    routePath,
  });
}
