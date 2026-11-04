import { Link } from "react-router-dom";

import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText } from "@swo/design-system/text";
import { DisplayValue, NO_VALUE } from "@swo/design-system/utils";

import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import DataSourceIcon from "~shared/components/custom-icons/CustomIcon";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatDate } from "~shared/hooks/useFormatDate";
import { getPropertyValue } from "~shared/utils/PropertiesUtils";

export function AzureDataSourceProperties({ entity }: { readonly entity: DatasourceDetailRead }) {
  const formatDate = useFormatDate();
  const tSharedDetails = useFixedT("shared:details");
  const tProperties = useFixedT("datasource:details:properties");

  return (
    <>
      <CardSection title={tSharedDetails("properties")}>
        <InPageHighlight direction="horizontal" style="block">
          <InPageHighlight.Item title={tProperties("connected_at")}>
            <BoldText color="grey-5">
              {entity?.details?.connected_at && (
                <DisplayValue value={formatDate(entity?.details?.connected_at)} />
              )}
            </BoldText>
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("parent")}>
            {entity?.parent?.id ? (
              <EntityReferenceCell
                primaryContent={
                  <Link to={`../../${entity?.parent?.id}/details`}>{entity?.parent?.name}</Link>
                }
                secondaryContent={entity?.parent?.datasource_id || NO_VALUE}
                secondaryContentMaxHeight={50}
                icon={<DataSourceIcon name={entity?.parent?.type || "unknown"} size={48} />}
              />
            ) : (
              NO_VALUE
            )}
          </InPageHighlight.Item>
        </InPageHighlight>
      </CardSection>
      <CardSection title={tSharedDetails("additionalIds")}>
        <InPageHighlight direction="horizontal" style="block">
          <InPageHighlight.Item title={tProperties("subscription_id")}>
            <BoldText color="grey-5">
              <DisplayValue value={getPropertyValue(entity, "subscription_id")} />
            </BoldText>
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("tenant_id")}>
            <BoldText color="grey-5">
              <DisplayValue value={getPropertyValue(entity, "tenant_id")} />
            </BoldText>
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("client_id")}>
            <BoldText color="grey-5">
              <DisplayValue value={getPropertyValue(entity, "client_id")} />
            </BoldText>
          </InPageHighlight.Item>
        </InPageHighlight>
      </CardSection>
    </>
  );
}
