import { useMemo } from "react";

import { useParams } from "react-router-dom";

import { EntityReference } from "@swo/design-system/entity-reference";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText, MediumText } from "@swo/design-system/text";
import { DisplayValue, NO_VALUE } from "@swo/design-system/utils";

import { useEntitlementsDetailsApi } from "~entitlements/api";
import { useFixedT } from "~shared/hooks/useFixedT";

export function EntitlementsGeneralDetails() {
  const { entitlementId } = useParams();
  const tProperties = useFixedT("shared:properties");
  const tSharedDetails = useFixedT("shared:details");
  const { data: entity } = useEntitlementsDetailsApi(entitlementId);

  const events = useMemo(
    () =>
      Object.entries(entity?.events ?? {})
        .filter(([, value]) => !!value?.by && !!value?.at)
        .map(([field, value]) => {
          return {
            name: tProperties(field),
            by: value?.by,
            at: value?.at,
          };
        }),
    [entity, tProperties],
  );

  return (
    <>
      <div>
        <MediumText size={4}>{tSharedDetails("additionalIds")}</MediumText>
        <InPageHighlight direction="horizontal" style="inline">
          <InPageHighlight.Item title={tProperties("linkedDataSource")}>
            <BoldText color="grey-5">
              <DisplayValue value={entity?.datasource_id} />
            </BoldText>
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("affiliate_external_id")}>
            <BoldText color="grey-5">
              <DisplayValue value={entity?.affiliate_external_id} />
            </BoldText>
          </InPageHighlight.Item>
        </InPageHighlight>
      </div>
      <InPageHighlight style="inline">
        {events?.map((event, i) => (
          <InPageHighlight.Item key={i} title={event.name}>
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
