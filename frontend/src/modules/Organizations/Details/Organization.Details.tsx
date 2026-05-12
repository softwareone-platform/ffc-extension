import { Card } from "@swo/design-system/card";
import { Link, Navigate, Route, Routes, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useOrganizationsApi } from "../hooks/useOrganizationsApi";
import { lazy, useEffect, useMemo } from "react";
import { Navigation } from "@swo/design-system/navigation";
import { Status } from "../../../shared/components/Status";
import { OrganizationRead } from "@swo/ffc-api-model";
import { EntityReference } from "@swo/design-system/entity-reference";
import { OrganizationsProvider } from "../providers/OrganizationsProvider";

const OrganizationGeneralDetails = lazy(() =>
  import("./General").then((m) => ({
    default: m.OrganizationGeneralDetails,
  })),
);
const OrganizationUsers = lazy(() =>
  import("./Users").then((m) => ({
    default: m.OrganizationUsers,
  })),
);
const OrganizationDataSources = lazy(() =>
  import("./DataSources").then((m) => ({
    default: m.OrganizationDataSources,
  })),
);

export function OrganizationDetails() {
  const { organizationId } = useParams();
  const { get } = useOrganizationsApi();
  //   const { get } = useJournalApi("RedirectOnError");
  //   const baseQueryKey = useBaseQueryKey("Journal");
  const entityQueryKey = useMemo(
    () => ["Organizations", "Details", organizationId],
    [organizationId],
  );
  const { data: entity, isLoading } = useQuery({
    queryKey: entityQueryKey,
    queryFn: () => get(organizationId!),
    select: (res) => res.data,
  });

  return (
    <OrganizationsProvider organization={entity!}>
      <Card className={"details-header"}>
        {entity && entity.id && (
          <EntityReference
            primaryContent={entity.name}
            secondaryContent={entity.id}
          />
        )}
        <Link to={"/"}>Back</Link>
      </Card>
      <Navigation.TopBar
        items={[
          { label: "General", path: `/${organizationId}/general` },
          { label: "Data Sources", path: `/${organizationId}/data-sources` },
          { label: "Users", path: `/${organizationId}/users` },
        ]}
      ></Navigation.TopBar>

      <Card>
        <Routes>
          <Route
            path="general"
            index
            element={<OrganizationGeneralDetails />}
          />
          <Route
            path="data-sources"
            index
            element={<OrganizationDataSources />}
          />
          <Route path="users" index element={<OrganizationUsers />} />
          <Route path="*" element={<Navigate to={"../general"} replace />} />
        </Routes>
      </Card>
    </OrganizationsProvider>
  );
}
