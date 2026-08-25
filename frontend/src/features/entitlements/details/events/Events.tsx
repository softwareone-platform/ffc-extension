import { useParams } from "react-router-dom";

import { EntitlementRead } from "~api/ffc-api-model/types.gen";
import { useEntitlementsDetailsApi } from "~features/entitlements/api/useEntitlementsDetailsApi";
import { EntityEvents } from "~shared/components/events/EntityEvents";

export function EntitlementEventsDetails() {
  const { entitlementId } = useParams();
  const { data: entity } = useEntitlementsDetailsApi(entitlementId);

  return entity ? <EntityEvents<EntitlementRead> entity={entity} /> : <></>;
}
