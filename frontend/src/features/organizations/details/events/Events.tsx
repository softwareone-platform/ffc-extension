import { useParams } from "react-router-dom";

import type { OrganizationRead } from "~api/ffc-api-model";
import { useOrganizationDetailsApi } from "~features/organizations/api/useOrganizationDetailsApi";
import { EntityEvents } from "~shared/components/events/EntityEvents";

export function OrganizationEventsDetails() {
  const { organizationId } = useParams();
  const { data: entity } = useOrganizationDetailsApi(organizationId);

  return entity ? <EntityEvents<OrganizationRead> entity={entity} /> : <></>;
}
