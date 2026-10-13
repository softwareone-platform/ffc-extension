import { useMemo } from "react";

import type {
  AuditEventsSchema,
  EntitlementsEventsSchema,
  OrganizationEventsSchema,
} from "~api/ffc-api-model";
import { EntityEvent, EventTimestamps } from "~shared/components/timestamps/EventTimestamps";
import { useFixedT } from "~shared/hooks/useFixedT";

import { CardSection } from "../CardSection";

type EntityEventsSchema = {
  events: EntitlementsEventsSchema | OrganizationEventsSchema | AuditEventsSchema;
};

export function EntityEvents<TEntity extends EntityEventsSchema>({
  entity,
}: {
  readonly entity: TEntity;
}) {
  const tTimestamps = useFixedT("shared:timestampsForm");
  const tSharedDetails = useFixedT("shared:details");
  const tProperties = useFixedT("shared:properties");

  const events: EntityEvent[] = useMemo(
    () =>
      Object.entries(entity?.events ?? {})
        .filter(([, value]) => !!value?.at)
        .map(([field, value]) => {
          return {
            name: tProperties(field),
            by: value?.by || { id: "system", name: tSharedDetails("system") },
            at: new Date(value?.at as string),
          };
        }),
    [entity, tProperties, tSharedDetails],
  );

  const columnNames = useMemo(
    () => [tTimestamps("event"), tTimestamps("triggeredBy"), tTimestamps("dateAndTime")],
    [tTimestamps],
  );

  return (
    <CardSection title={tSharedDetails("events")}>
      <EventTimestamps events={events} columnNames={columnNames} />
    </CardSection>
  );
}
