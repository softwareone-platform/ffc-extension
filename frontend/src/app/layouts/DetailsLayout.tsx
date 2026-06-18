import { ReactNode } from "react";

import { useParams, useResolvedPath } from "react-router-dom";

import { PageShell } from "~shared/components/page-shell";

type Props = {
  paramKey: string;
  renderHeader: (entityId: string, backUrl: string) => ReactNode;
  children: ReactNode;
};

// Used by per-feature entries; the standalone app uses MainLayout instead.
export function DetailsLayout({ paramKey, renderHeader, children }: Readonly<Props>) {
  const params = useParams();
  const entityId = params[paramKey];
  const basePath = useResolvedPath("").pathname.replace(/\/$/, "");
  const backUrl = basePath.replace(/\/[^/]+$/, "") || "/";

  return (
    <PageShell>
      {entityId ? renderHeader(entityId, backUrl) : null}
      <PageShell.Content>{children}</PageShell.Content>
    </PageShell>
  );
}
