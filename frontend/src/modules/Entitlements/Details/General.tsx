import {
  DisplayValue,
  NO_VALUE,
  useLocalisation,
} from "@swo/design-system/utils";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText, MediumText, RegularText } from "@swo/design-system/text";
// import { Timestamps } from "@swo/mp-timestamps";
import { useEntitlementsApi } from "../hooks/useEntitlementsApi";
import { useFixedT } from "../../../shared/hooks/useFixedT";
import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { EntityReference } from "@swo/design-system/entity-reference";
// const { formatDate, formatTime } = useLocalisation();

export function EntitlementGeneralDetails() {
  const { entitlementId } = useParams();
  const { get } = useEntitlementsApi();
  const tProperties = useFixedT("shared:properties");
  const tSharedDetails = useFixedT("shared:details");
  //   const { get } = useJournalApi("RedirectOnError");
  //   const baseQueryKey = useBaseQueryKey("Journal");
  const entityQueryKey = useMemo(
    () => ["Entitlements", "Details", entitlementId],
    ["Entitlements", entitlementId],
  );
  const { data: entity, isLoading } = useQuery({
    queryKey: entityQueryKey,
    queryFn: () => get(entitlementId!),
    select: (res) => res.data,
  });

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

  const columnNames = useMemo(
    () => [
      tProperties("event"),
      tProperties("triggeredBy"),
      tProperties("dateAndTime"),
    ],
    [tProperties],
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
      {/* <Timestamps
        events={events}
        columnNames={columnNames}
        componentTitle={tProperties("title")}
      /> */}
      {/* <div>
        <MediumText size={4}>{tSharedDetails("timestamps")}</MediumText>
        <InPageHighlight direction="vertical">
          <InPageHighlight.Item title={tProperties("currency")}>
            <DisplayValue value={entity?.currency} />
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("billingCurrency")}>
            <DisplayValue value={entity?.billing_currency} />
          </InPageHighlight.Item>
        </InPageHighlight>
      </div> */}
    </>
  );
}
