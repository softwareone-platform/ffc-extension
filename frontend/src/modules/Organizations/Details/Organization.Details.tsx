import { Card } from "@swo/design-system/card";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useOrganizationsApi } from "../hooks/useOrganizationsApi";
import { useMemo } from "react";

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
        organizationId!,
        // new RqlQuery<Entity>().expand(
        //   "event.created.at",
        //   "audit.updated.at",
        //   "owner.address.country",
        //   "audit",
        // ),
      ),
    select: (res) => res.data,
    // refetchInterval(query) {
    //   const status = query.state.data?.data?.status;
    //   const lastUpdate = query.state.data?.data?.audit?.updated?.at;
    //   return status === "Generating" ||
    //     status === "Validating" ||
    //     status === "Resetting"
    //     ? getPollingTime(lastUpdate)
    //     : false;
    // },
  });

  return (
    <>
      <Card>Top nav {organizationId}</Card>

      <Card>
        <h1>Organization details</h1>
        <p>This is where the details of the organization would be displayed.</p>
      </Card>
    </>
  );
}
