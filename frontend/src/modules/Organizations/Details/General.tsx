import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useOrganizationsApi } from "../hooks/useOrganizationsApi";
import { useMemo } from "react";

import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { MediumText, RegularText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";
import { useFixedT } from "../../../shared/hooks/useFixedT";

export function OrganizationGeneralDetails() {
  const { organizationId } = useParams();
  const { get } = useOrganizationsApi();
  //   const { get } = useJournalApi("RedirectOnError");
  //   const baseQueryKey = useBaseQueryKey("Journal");
  const entityQueryKey = useMemo(
    () => ["Organizations", "Details", organizationId],
    ["Organizations", organizationId],
  );
  const { data: entity, isLoading } = useQuery({
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

  const tSharedDetails = useFixedT("shared:details");

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
            <DisplayValue value={mockedExpensesInfo.expenses_last_month} />{" "}
            {entity?.currency}
          </dd>
          <dt>{tProperties("expensesThisMonth")}</dt>
          <dd>
            <DisplayValue
              value={mockedExpensesInfo.expenses_so_far_this_month}
            />{" "}
            {entity?.currency}
          </dd>
          <dt>{tProperties("forecastThisMonth")}</dt>
          <dd>
            <DisplayValue
              value={mockedExpensesInfo.expenses_forecast_this_month}
            />{" "}
            {entity?.currency}
          </dd>
          <dt>{tProperties("possibleSavings")}</dt>
          <dd>
            <DisplayValue value={mockedExpensesInfo.possible_savings} />{" "}
            {entity?.currency}
          </dd>
        </dl>
      </div>
    </>
  );
}
