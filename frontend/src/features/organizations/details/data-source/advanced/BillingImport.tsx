import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { Status } from "~shared/components/entity-status-chip";
import { useDateDistance } from "~shared/hooks/useDateDistance";
import { useFixedT } from "~shared/hooks/useFixedT";

export function BillingImport({ entity }: { readonly entity: DatasourceDetailRead }) {
  const dateDistance = useDateDistance();
  const tSharedDetails = useFixedT("shared:details");

  const tProperties = useFixedT("datasource:details:properties");

  return (
    <CardSection title={tSharedDetails("billing_import")}>
      <InPageHighlight direction="horizontal" style="inline">
        <InPageHighlight.Item title={tProperties("last_report_processed_at")}>
          <BoldText color="grey-5">
            <DisplayValue value={dateDistance(entity?.billing?.last_report_processed_at || "")} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("billing_last_attempt")}>
          <BoldText color="grey-5">
            <DisplayValue value={dateDistance(entity?.billing?.last_attempt_at || "")} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("status")}>
          <BoldText color="grey-5">
            <Status status={entity?.billing?.status ?? ""} />
          </BoldText>
        </InPageHighlight.Item>
      </InPageHighlight>
    </CardSection>
  );
}
