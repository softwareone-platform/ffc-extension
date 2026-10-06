import { useParams } from "react-router-dom";

import { DisplayValue } from "@swo/design-system/utils";

import { useOrganizationDetailsApi } from "~organizations/api";
import { useFixedT } from "~shared/hooks/useFixedT";

import "./General.scss";

import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText } from "@swo/design-system/text";

import { CardSection } from "~shared/components/CardSection";

export function OrganizationGeneralDetails() {
  const { organizationId } = useParams();
  const { data: entity } = useOrganizationDetailsApi(organizationId);
  const tSharedDetails = useFixedT("shared:details");

  const tProperties = useFixedT("organization:details:general:properties");

  return (
    <CardSection title={tSharedDetails("additionalIds")}>
      <InPageHighlight direction="horizontal" style="block">
        <InPageHighlight.Item title={tProperties("operations_external_id")}>
          <BoldText color="grey-5">
            <DisplayValue value={entity?.operations_external_id} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("linked_organization_id")}>
          <BoldText color="grey-5">
            <DisplayValue value={entity?.linked_organization_id} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("currency")}>
          <BoldText color="grey-5">
            <DisplayValue value={entity?.currency} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("billing_currency")}>
          <BoldText color="grey-5">
            <DisplayValue value={entity?.billing_currency} />
          </BoldText>
        </InPageHighlight.Item>
      </InPageHighlight>
    </CardSection>
  );
}
