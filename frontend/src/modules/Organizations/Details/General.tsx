import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useOrganizationsApi } from "../hooks/useOrganizationsApi";
import { useMemo } from "react";

export function OrganizationGeneralDetails() {
  const { organizationId } = useParams();
  const { get } = useOrganizationsApi();
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
    select: (res) => res.data,
  });
  return (
    <>
      <h1>Organization details</h1>
      <p>Top nav {organizationId} {entity?.name}{" "}</p>
      <p>This is where the details of the organization would be displayed.</p>
      <pre>{}</pre>
    </>
  );
}
