import { Button } from "@swo/design-system/button";
import { Card } from "@swo/design-system/card";
import { EntityReference } from "@swo/design-system/entity-reference";
import { lazy, useMemo } from "react";
import { Navigation } from "@swo/design-system/navigation";
import { OrganizationsProvider } from "../providers/OrganizationsProvider";
import { useOrganizationsApi } from "../hooks/useOrganizationsApi";
import { useQuery } from "@tanstack/react-query";

import {
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";

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

  let navigate = useNavigate();

  return (
    <OrganizationsProvider organization={entity!}>
      <Card className={"details-header"}>
        {entity && entity.id && (
          <EntityReference
            primaryContent={entity.name}
            secondaryContent={entity.id}
          />
        )}
        <Button type="outline" onClick={() => navigate("/")}>
          Back
        </Button>
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
