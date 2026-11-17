import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { InlineNotification } from "@swo/design-system/notification";
import { BoldText, RegularText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { Status } from "~shared/components/entity-status-chip";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatDate } from "~shared/hooks/useFormatDate";

import style from "./AdvancedDetails.module.scss";

export function MonitoringMetrics({ entity }: { readonly entity: DatasourceDetailRead }) {
  const formatDate = useFormatDate();
  const tSharedDetails = useFixedT("shared:details");

  const tProperties = useFixedT("datasource:details:properties");

  return (
    <CardSection
      className={style["monitoring-metrics"]}
      title={tSharedDetails("monitoring_metrics")}
    >
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
      {entity?.metrics?.error && (
        <div className={style["monitoring-metrics-error"]}>
          <InlineNotification status="error">
            <BoldText color="grey-5">{tSharedDetails("errorDetails")}</BoldText>
            <RegularText color="grey-5">
              <DisplayValue value={entity?.metrics?.error} />
            </RegularText>
          </InlineNotification>
        </div>
      )}
    </CardSection>
  );
}
