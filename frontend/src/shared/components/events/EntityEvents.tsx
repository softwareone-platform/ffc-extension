import { useMemo } from "react";

import { EntityReference } from "@swo/design-system/entity-reference";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { MediumText } from "@swo/design-system/text";
import { NO_VALUE } from "@swo/design-system/utils";

import {
  AuditEventsSchema,
  EntitlementsEventsSchema,
  OrganizationEventsSchema,
} from "~api/ffc-api-model/types.gen";
import { useFixedT } from "~shared/hooks/useFixedT";

type EntityEventsSchema = {
  events: EntitlementsEventsSchema | OrganizationEventsSchema | AuditEventsSchema;
};

export function EntityEvents<TEntity extends EntityEventsSchema>({
  entity,
}: {
  readonly entity: TEntity;
}) {
  const tSharedDetails = useFixedT("shared:details");
  const tProperties = useFixedT("shared:properties");

  const events = useMemo(
    () =>
      Object.entries(entity?.events ?? {})
        .filter(([, value]) => !!value?.at)
        .map(([field, value]) => {
          return {
            name: tProperties(field),
            by: value?.by || { name: tSharedDetails("system") },
            at: value?.at,
          };
        }),
    [entity, tProperties],
  );

  return (
    <>
      <MediumText size={4}>{tSharedDetails("events")}</MediumText>
      <InPageHighlight style="block">
        {events?.map((event, i) => (
          <InPageHighlight.Item key={event.name} title={event.name}>
            {event.at ? (
              <EntityReference
                primaryContent={event.by?.name}
                secondaryContent={event.at}
                isPrimaryContentBold={true}
              />
            ) : (
              NO_VALUE
            )}
          </InPageHighlight.Item>
        ))}
      </InPageHighlight>
    </>
  );
}
