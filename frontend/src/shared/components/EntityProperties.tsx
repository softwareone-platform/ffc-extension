import { EntityReference } from "@swo/design-system/entity-reference";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText } from "@swo/design-system/text";

import { AddWizardForm } from "~entitlements/create-entitlement-wizard/CreateEntitlement.Schema";
import { useFixedT } from "~shared/hooks/useFixedT";

import CustomIcon from "./custom-icons/CustomIcon";
import { Status } from "./entity-status-chip";

export interface EntityPropertiesProps {
  readonly entity: AddWizardForm;
}

export function EntityProps({ entity }: EntityPropertiesProps) {
  const tProperties = useFixedT("entitlements:addWizard:properties");

  return (
    <InPageHighlight
      style="inline"
      mode="dense"
      direction="vertical"
      className={"in-page-highlight-form"}
    >
      {entity?.id && (
        <InPageHighlight.Item title={tProperties("entitlementId")}>
          <BoldText color="brand-type">
            {entity.id} <Status<{ status: string }> item={{ status: "New" }}></Status>
          </BoldText>
        </InPageHighlight.Item>
      )}
      <InPageHighlight.Item title={tProperties("affiliate")}>
        {entity?.affiliate && (
          <EntityReference
            primaryContent={entity.affiliate.name}
            secondaryContent={entity.affiliate.id}
            isPrimaryContentBold={false}
            icon={<CustomIcon name={entity.affiliate.integration} size={44} />}
          />
        )}
      </InPageHighlight.Item>
      <InPageHighlight.Item title={tProperties("dataSource:id")}>
        <BoldText color="brand-type">{entity?.dataSource?.id}</BoldText>
      </InPageHighlight.Item>
      <InPageHighlight.Item title={tProperties("dataSource:affiliateExternalId")}>
        <BoldText color="brand-type">{entity?.dataSource?.affiliate_external_id}</BoldText>
      </InPageHighlight.Item>
    </InPageHighlight>
  );
}
