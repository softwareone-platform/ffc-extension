import { useMemo } from "react";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { DisplayValue } from "@swo/design-system/utils";

import { useOrganizationsApi } from "~organizations/api";
import { useFixedT } from "~shared/hooks/useFixedT";

import "./General.scss";

export function OrganizationGeneralDetails() {
  const { organizationId } = useParams();
  const { get } = useOrganizationsApi();
  const entityQueryKey = useMemo(
    () => ["Organizations", "Details", organizationId],
    [organizationId],
  );
  const { data: entity } = useQuery({
    queryKey: entityQueryKey,
    queryFn: () => get(organizationId!),
    select: (res) => res.data,
  });

  const mockedExpensesInfo = {
    limit: 123,
    expenses_last_month: 123123.12,
    expenses_so_far_this_month: 123123.12,
    expenses_forecast_this_month: 123123.12,
    possible_savings: 123123.12,
  };

  const tProperties = useFixedT("organization:details:general:properties");
  return (
    <>
      <div className={"organization-details-general"}>
        <dl className={"properties-section"}>
          <dt>{tProperties("limit")}</dt>
          <dd>
            <DisplayValue value={mockedExpensesInfo.limit} /> {entity?.currency}
          </dd>
          <dt>{tProperties("expensesLastMonth")}</dt>
          <dd>
            <DisplayValue value={mockedExpensesInfo.expenses_last_month} /> {entity?.currency}
          </dd>
          <dt>{tProperties("expensesThisMonth")}</dt>
          <dd>
            <DisplayValue value={mockedExpensesInfo.expenses_so_far_this_month} />{" "}
            {entity?.currency}
          </dd>
          <dt>{tProperties("forecastThisMonth")}</dt>
          <dd>
            <DisplayValue value={mockedExpensesInfo.expenses_forecast_this_month} />{" "}
            {entity?.currency}
          </dd>
          <dt>{tProperties("possibleSavings")}</dt>
          <dd>
            <DisplayValue value={mockedExpensesInfo.possible_savings} /> {entity?.currency}
          </dd>
        </dl>
      </div>
    </>
  );
}
