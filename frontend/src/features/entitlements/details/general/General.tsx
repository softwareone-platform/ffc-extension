import { useParams } from "react-router-dom";

import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText, MediumText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { useEntitlementsDetailsApi } from "~entitlements/api";
import { useFixedT } from "~shared/hooks/useFixedT";

export function EntitlementsGeneralDetails() {
  const { entitlementId } = useParams();
  const tProperties = useFixedT("shared:properties");
  const tSharedDetails = useFixedT("shared:details");
  const { data: entity } = useEntitlementsDetailsApi(entitlementId);

  return (
    <div>
      <MediumText size={4}>{tSharedDetails("additionalIds")}</MediumText>
      <InPageHighlight direction="horizontal" style="block">
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
  );
}
