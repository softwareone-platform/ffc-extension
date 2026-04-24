import { Card } from "@swo/design-system/card";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useOrganizationsApi } from "../hooks/useOrganizationsApi";
import { useEffect, useMemo } from "react";
import { Navigation } from "@swo/design-system/navigation";
import { Status } from "../../../shared/components/Status";
import { OrganizationRead } from "@swo/ffc-api-model";

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
          { label: "General", path: `/${entity?.id}` },
          { label: "Senders", path: "/email-settings/senders" },
        ]}
      ></Navigation.TopBar>

      <Card>
        <h1>Organization details</h1>
        <p>
          Top nav {organizationId} {entity?.name}{" "}
        </p>
        <p>This is where the details of the organization would be displayed.</p>
        <pre>{}</pre>
      </Card>
    </>
  );
}
