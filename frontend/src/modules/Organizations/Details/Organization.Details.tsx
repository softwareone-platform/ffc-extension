import { Card } from "@swo/design-system/card";
import { Link, Navigate, Route, Routes, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useOrganizationsApi } from "../hooks/useOrganizationsApi";
import { lazy, useEffect, useMemo } from "react";
import { Navigation } from "@swo/design-system/navigation";
import { Status } from "../../../shared/components/Status";
import { OrganizationRead } from "@swo/ffc-api-model";

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
    ["Organizations", organizationId],
  );
  const { data: entity, isLoading } = useQuery({
    queryKey: entityQueryKey,
    queryFn: () =>
      get(
        organizationId!
      ),
    select: (res) => res.data
  });

  useEffect(() => {
    console.log(entity);
  }, [entity]);

  return (
    <>
      <Card className={"organization-details-header"}>
        {entity && entity.id && (
          <>
            <h1>{entity?.name}</h1>
            <Status<OrganizationRead> item={entity}></Status>
          </>
        )}
        <Link to={"/"}>Back</Link>
      </Card>
      <Navigation.TopBar
        items={[
          { label: "General", path: `/${entity?.id}/general` },
          { label: "Data Sources", path: `/${entity?.id}/data-sources` },
          { label: "Users", path: `/${entity?.id}/users` }
          // { label: "Details", path: `/${entity?.id}/details` },
          // { label: "Audit Trail", path: `/${entity?.id}/audit-trail` },
        ]}
      ></Navigation.TopBar>

      <Card>
        <Routes>
          <Route
            path="general"
            index
            element={<OrganizationGeneralDetails />}
          />
          <Route path="data-sources" index element={<OrganizationDataSources />} />
          <Route path="users" index element={<OrganizationUsers />} />
          <Route path="*" element={<Navigate to={"../general"} replace />} />
        </Routes>
      </Card>
    </>
  );
}
