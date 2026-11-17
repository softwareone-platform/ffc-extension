import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatDate } from "~shared/hooks/useFormatDate";

export function UnknownDataSourceProperties({ entity }: { readonly entity: DatasourceDetailRead }) {
  const tSharedDetails = useFixedT("shared:details");
  const tProperties = useFixedT("datasource:details:properties");
  const formatDate = useFormatDate();

  return (
    <CardSection title={tSharedDetails("properties")}>
      <InPageHighlight direction="horizontal" style="block">
        <InPageHighlight.Item title={tProperties("connected_at")}>
          <BoldText color="grey-5">
            {entity?.details?.connected_at && (
              <DisplayValue value={formatDate(entity?.details?.connected_at)} />
            )}
          </BoldText>
        </InPageHighlight.Item>
      </InPageHighlight>
    </CardSection>
  );
}
