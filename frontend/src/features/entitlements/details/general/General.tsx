import { useParams } from "react-router-dom";

import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText } from "@swo/design-system/text";
import { DisplayValue, NO_VALUE } from "@swo/design-system/utils";

import { useEntitlementsDetailsApi } from "~entitlements/api";
import { CardSection } from "~shared/components/CardSection";
import { useFixedT } from "~shared/hooks/useFixedT";

export function EntitlementsGeneralDetails() {
  const { entitlementId } = useParams();
  const tProperties = useFixedT("shared:properties");
  const tSharedDetails = useFixedT("shared:details");
  const { data: entity } = useEntitlementsDetailsApi(entitlementId);

  return (
    <CardSection title={tSharedDetails("additionalIds")}>
      <InPageHighlight direction="horizontal" style="block">
        <InPageHighlight.Item title={tProperties("linkedDataSource")}>
          <BoldText color="grey-5">
            <DisplayValue value={entity?.linked_datasource_id || NO_VALUE} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("affiliate_external_id")}>
          <BoldText color="grey-5">
            <DisplayValue value={entity?.affiliate_external_id || NO_VALUE} />
          </BoldText>
        </InPageHighlight.Item>
      </InPageHighlight>
    </CardSection>
  );
}
