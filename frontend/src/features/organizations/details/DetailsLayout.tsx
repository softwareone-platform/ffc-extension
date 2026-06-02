import { useParams, useResolvedPath } from "react-router-dom";

import { PageShell } from "~shared/components/page-shell";

import { OrganizationDetailsHeader } from "../components/OrganizationDetailsHeader";
import { OrganizationDetailsContent } from "./DetailsContent";

/**
 * Full-chrome organization details layout. Used by the per-feature entry
 * (`entries/organizations.tsx`) where there is no surrounding `MainLayout`
 * to provide the header. The standalone app uses `OrganizationDetailsContent`
 * directly and lets `MainLayout` render the header.
 */
export function OrganizationDetailsLayout() {
  const { organizationId } = useParams();
  const basePath = useResolvedPath("").pathname.replace(/\/$/, "");
  const backUrl = basePath.replace(/\/[^/]+$/, "") || "/";

  return (
    <PageShell>
      {organizationId ? (
        <OrganizationDetailsHeader organizationId={organizationId} backUrl={backUrl} />
      ) : null}
      <PageShell.Content>
        <OrganizationDetailsContent />
      </PageShell.Content>
    </PageShell>
  );
}
