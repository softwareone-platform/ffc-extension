import { Avatar } from "@swo/design-system/avatar";
import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { Navigation } from "@swo/design-system/navigation";
import { Skeleton } from "@swo/design-system/skeleton";
import { DisplayValue, NO_VALUE } from "@swo/design-system/utils";

import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatMoney } from "~shared/utils/NumberUtils";

import { useDataSourceApi } from "../api/useDataSourceApi";
import { useOrganizationDetailsApi } from "../api/useOrganizationDetailsApi";
import style from "./OrganizationHighlights.module.scss";

export function DataSourceHighlights({
  dataSourceId,
  organizationId,
}: {
  readonly organizationId: string;
  readonly dataSourceId: string;
}) {
  const { data: organization } = useOrganizationDetailsApi(organizationId);
  const { data: dataSource } = useDataSourceApi(organizationId, dataSourceId);
  const tProperties = useFixedT("organization:details:expenses:properties");
  const format = useFormatMoney(organization?.currency, false);

  return (
    <Navigation.Highlights>
      {dataSource?.id ? (
        <InPageHighlight style="inline">
          {organization?.id ? (
            <InPageHighlight.Item title="">
              <div className={style["client-info"]}>
                <EntityReferenceCell
                  primaryContent={organization.name}
                  secondaryContent={organization.id || NO_VALUE}
                  secondaryContentMaxHeight={50}
                  icon={
                    <Avatar
                      size={32}
                      shape="square"
                      isToUseJdenticon={true}
                      jdenticonValue={organization.id ?? organization.name ?? ""}
                    />
                  }
                />
              </div>
            </InPageHighlight.Item>
          ) : null}
          <InPageHighlight.Item title={tProperties("resourcesChargedThisMonth")}>
            <DisplayValue value={dataSource.resources_charged_this_month ?? 0} />{" "}
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("expensesThisMonth")}>
            <DisplayValue
              value={dataSource.expenses_so_far_this_month ?? 0}
              transform={format}
              context="financial"
            />{" "}
            {organization?.currency}
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("forecastThisMonth")}>
            <DisplayValue
              value={dataSource?.expenses_forecast_this_month ?? 0}
              transform={format}
              context="financial"
            />{" "}
            {organization?.currency}
          </InPageHighlight.Item>
        </InPageHighlight>
      ) : (
        <Skeleton rows={1} cols={1} />
      )}
    </Navigation.Highlights>
  );
}
