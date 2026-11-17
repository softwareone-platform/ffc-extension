import { useParams } from "react-router-dom";

import { CardSection } from "~shared/components/CardSection";
import { useFixedT } from "~shared/hooks/useFixedT";

import { EventLogsGrid } from "./EventLogsGrid";

export function OrganizationLogsDetails() {
  const { organizationId } = useParams();

  const tSharedDetails = useFixedT("shared:details");

  return (
    <CardSection title={tSharedDetails("logs")}>
      {organizationId && <EventLogsGrid organizationId={organizationId} />}
    </CardSection>
  );
}
