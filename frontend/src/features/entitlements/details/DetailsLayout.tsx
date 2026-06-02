import { Outlet, useParams, useResolvedPath } from "react-router-dom";

import { PageShell } from "~shared/components/page-shell";

import { EntitlementDetailsHeader } from "../components/EntitlementDetailsHeader";

/**
 * Full-chrome entitlement details layout. Used by the per-feature entry
 * (`entries/entitlements.tsx`) where there is no surrounding `MainLayout`
 * to provide the header. The standalone app skips this layout and lets
 * `MainLayout` render the header above the matched detail page directly.
 */
export function EntitlementsDetailsLayout() {
  const { entitlementId } = useParams();
  const basePath = useResolvedPath("").pathname.replace(/\/$/, "");
  const backUrl = basePath.replace(/\/[^/]+$/, "") || "/";

  return (
    <PageShell>
      {entitlementId ? (
        <EntitlementDetailsHeader entitlementId={entitlementId} backUrl={backUrl} />
      ) : null}
      <PageShell.Content>
        <Outlet />
      </PageShell.Content>
    </PageShell>
  );
}
