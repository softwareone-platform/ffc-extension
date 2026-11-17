import { InlineNotification } from "@swo/design-system/notification";

import { CardSection } from "~shared/components/CardSection";
import { useFixedT } from "~shared/hooks/useFixedT";

export function DataSourceError() {
  const tSharedDetails = useFixedT("shared:details");

  return (
    <CardSection title={tSharedDetails("properties")}>
      <InlineNotification status="error">{tSharedDetails("noDataSource")}</InlineNotification>
    </CardSection>
  );
}
