import { Avatar } from "@swo/design-system/avatar";
import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { Navigation } from "@swo/design-system/navigation";
import { Skeleton } from "@swo/design-system/skeleton";
import { DisplayValue, NO_VALUE } from "@swo/design-system/utils";

import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatMoney } from "~shared/utils/NumberUtils";

import { useOrganizationDetailsApi } from "../api";
import style from "./OrganizationHighlights.module.scss";

export function OrganizationHighlights({ organizationId }: { readonly organizationId: string }) {
  const { data: entity } = useOrganizationDetailsApi(organizationId);
  const tProperties = useFixedT("organization:details:expenses:properties");
  const format = useFormatMoney(entity?.currency, false);

  return (
    <Navigation.Highlights>
      {entity?.id ? (
        <InPageHighlight style="inline">
          {entity?.client?.id ? (
            <InPageHighlight.Item title="">
              <div className={style["client-info"]}>
                <EntityReferenceCell
                  primaryContent={entity.client?.name}
                  secondaryContent={entity.client?.external_id || NO_VALUE}
                  secondaryContentMaxHeight={50}
                  icon={
                    entity.client?.icon ? (
                      <Avatar
                        size={32}
                        shape="square"
                        imageSrc={"/public/" + entity.client?.icon}
                      />
                    ) : undefined
                  }
                />
              </div>
            </InPageHighlight.Item>
          ) : null}
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
