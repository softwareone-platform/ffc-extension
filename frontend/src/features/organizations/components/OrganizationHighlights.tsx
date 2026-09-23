import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { Navigation } from "@swo/design-system/navigation";
import { Skeleton } from "@swo/design-system/skeleton";
import { DisplayValue } from "@swo/design-system/utils";

import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatMoney } from "~shared/utils/NumberUtils";

import { useOrganizationDetailsApi } from "../api";

export function OrganizationHighlights({ organizationId }: { readonly organizationId: string }) {
  const { data: entity } = useOrganizationDetailsApi(organizationId);
  const tProperties = useFixedT("organization:details:expenses:properties");
  const format = useFormatMoney(entity?.currency, false);

  return (
    <Navigation.Highlights>
      {entity?.id ? (
        <InPageHighlight style="inline">
          <InPageHighlight.Item title={tProperties("limit")}>
            <DisplayValue
              value={Number.parseFloat(entity?.expenses_info?.limit || "0")}
              transform={format}
              context="financial"
            />{" "}
            {entity?.currency}
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("expensesThisMonth")}>
            <DisplayValue
              value={Number.parseFloat(entity?.expenses_info?.expenses_this_month || "0")}
              transform={format}
              context="financial"
            />{" "}
            {entity?.currency}
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("forecastThisMonth")}>
            <DisplayValue
              value={Number.parseFloat(entity?.expenses_info?.expenses_this_month_forecast || "0")}
              transform={format}
              context="financial"
            />{" "}
            {entity?.currency}
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("possibleSavings")}>
            <DisplayValue
              value={Number.parseFloat(entity?.expenses_info?.possible_monthly_saving || "0")}
              transform={format}
              context="financial"
            />{" "}
            {entity?.currency}
          </InPageHighlight.Item>
        </InPageHighlight>
      ) : (
        <Skeleton rows={1} cols={1} />
      )}
    </Navigation.Highlights>
  );
}
