import { Outlet, useParams } from "react-router-dom";

import { Card } from "@swo/design-system/card";
import { Navigation } from "@swo/design-system/navigation";

import { ContentType, useContentType } from "~features/organizations/hooks/useContentType";
import { useTopBarItems } from "~features/organizations/hooks/useTopBarItems";
import { useOrganizationDetailsApi } from "~organizations/api";

import { DataSourceHighlights } from "../components/DataSourceHighlights";
import { OrganizationHighlights } from "../components/OrganizationHighlights";
import { OrganizationsProvider } from "../providers/OrganizationsProvider";

// Inner content for organization details. Outer chrome comes from MainLayout.
export function OrganizationDetailsContent() {
  const { organizationId, dataSourceId } = useParams();
  const { data: entity, isLoading } = useOrganizationDetailsApi(organizationId);
  const topBarItems = useTopBarItems({ entity, routeId: dataSourceId });
  const contentType = useContentType();

  if (!organizationId) return null;

  return (
    <>
      {contentType === ContentType.DataSource && (
        <DataSourceHighlights organizationId={organizationId} dataSourceId={dataSourceId ?? ""} />
      )}
      {contentType === ContentType.Organization && (
        <OrganizationHighlights organizationId={organizationId} />
      )}
      <OrganizationsProvider organization={entity!}>
        <Navigation.TopBar items={isLoading ? [] : topBarItems} />
        <Card>
          <Outlet />
        </Card>
      </OrganizationsProvider>
    </>
  );
}
