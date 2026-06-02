import { useParams, useResolvedPath } from "react-router-dom";

import { PageShell } from "~shared/components/page-shell";

import { EntitlementDetailsHeader } from "../components/EntitlementDetailsHeader";
import { EntitlementDetailsContent } from "./DetailsContent";

/**
 * Full-chrome entitlement details layout. Used by the per-feature entry
 * (`entries/entitlements.tsx`) where there is no surrounding `MainLayout`
 * to provide the header. The standalone app uses `EntitlementDetailsContent`
 * directly and lets `MainLayout` render the header.
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
        <EntitlementDetailsContent />
      </PageShell.Content>
    </PageShell>
  );
}
