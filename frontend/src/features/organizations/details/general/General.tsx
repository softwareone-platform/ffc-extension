import { useParams } from "react-router-dom";

import { DisplayValue } from "@swo/design-system/utils";

import { useOrganizationDetailsApi } from "~organizations/api";
import { useFixedT } from "~shared/hooks/useFixedT";

import "./General.scss";

import { useFormatMoney } from "~shared/utils/NumberUtils";

export function OrganizationGeneralDetails() {
  const { organizationId } = useParams();
  const { data: entity } = useOrganizationDetailsApi(organizationId);
  const format = useFormatMoney(entity?.currency, false);

  const tProperties = useFixedT("organization:details:general:properties");

  return (
    <>
      <div className={"organization-details-general"}>
        <dl className={"properties-section"}>
          <dt>{tProperties("limit")}</dt>
          <dd>
            <DisplayValue
              value={Number.parseFloat(entity?.expenses_info?.limit || "0")}
              transform={format}
              context="financial"
            />{" "}
            {entity?.currency}
          </dd>
          <dt>{tProperties("expensesThisMonth")}</dt>
          <dd>
            <DisplayValue
              value={Number.parseFloat(entity?.expenses_info?.expenses_this_month || "0")}
              transform={format}
              context="financial"
            />{" "}
            {entity?.currency}
          </dd>
          <dt>{tProperties("forecastThisMonth")}</dt>
          <dd>
            <DisplayValue
              value={Number.parseFloat(entity?.expenses_info?.expenses_this_month_forecast || "0")}
              transform={format}
              context="financial"
            />{" "}
            {entity?.currency}
          </dd>
          <dt>{tProperties("possibleSavings")}</dt>
          <dd>
            <DisplayValue
              value={Number.parseFloat(entity?.expenses_info?.possible_monthly_saving || "0")}
              transform={format}
              context="financial"
            />{" "}
            {entity?.currency}
          </dd>
        </dl>
      </div>
    </>
  );
}
