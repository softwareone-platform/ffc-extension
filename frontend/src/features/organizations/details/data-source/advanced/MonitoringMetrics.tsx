import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { Status } from "~shared/components/entity-status-chip";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatDate } from "~shared/hooks/useFormatDate";

export function MonitoringMetrics({ entity }: { readonly entity: DatasourceDetailRead }) {
  const formatDate = useFormatDate();
  const tSharedDetails = useFixedT("shared:details");

  const tProperties = useFixedT("datasource:details:properties");

  return (
    <CardSection title={tSharedDetails("monitoring_metrics")}>
      <InPageHighlight direction="horizontal" style="inline">
        <InPageHighlight.Item title={tProperties("metrics_last_retrieval")}>
          <BoldText color="grey-5">
            <DisplayValue value={formatDate(entity?.metrics?.last_retrieval_at || "")} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("metrics_last_attempt")}>
          <BoldText color="grey-5">
            <DisplayValue value={formatDate(entity?.metrics?.last_attempt_at || "")} />
          </BoldText>
        </InPageHighlight.Item>
        <InPageHighlight.Item title={tProperties("status")}>
          <BoldText color="grey-5">
            <Status status={entity?.metrics?.status ?? ""} />
          </BoldText>
        </InPageHighlight.Item>
      </InPageHighlight>
    </CardSection>
  );
}
