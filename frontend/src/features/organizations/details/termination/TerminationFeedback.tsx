import { useParams } from "react-router-dom";

import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { InlineNotification } from "@swo/design-system/notification";
import { BoldText, RegularText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { useOrganizationDetailsApi } from "~organizations/api";
import { CardSection } from "~shared/components/CardSection";
import { useFixedT } from "~shared/hooks/useFixedT";

import styles from "./TerminationFeedback.module.scss";

export function OrganizationTerminationFeedback() {
  const { organizationId } = useParams();
  const { data: entity } = useOrganizationDetailsApi(organizationId);
  const tTermination = useFixedT("organization:details:termination");
  const tReason = useFixedT("organization:details:termination:reason");

  const terminationFeedback = entity?.termination_feedback;

  const tProperties = useFixedT("organization:details:termination:properties");

  return (
    <CardSection title={tTermination("title")}>
      {terminationFeedback ? (
        <InPageHighlight direction="vertical" style="block">
          <InPageHighlight.Item title={tProperties("reason")}>
            <BoldText color="grey-5">
              <DisplayValue value={tReason(terminationFeedback?.reason || "unknown")} />
            </BoldText>
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("comment")}>
            <div className={styles.termination__comment}>
              <DisplayValue value={terminationFeedback?.comments} />
            </div>
          </InPageHighlight.Item>
        </InPageHighlight>
      ) : (
        <InlineNotification status="warning" isToShowCloseButton={false} width="auto">
          <RegularText color="brand-type">{tTermination("feedbackMissing")}</RegularText>
        </InlineNotification>
      )}
    </CardSection>
  );
}
