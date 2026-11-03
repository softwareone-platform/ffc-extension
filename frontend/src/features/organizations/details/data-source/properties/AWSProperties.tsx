import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { BoldText } from "@swo/design-system/text";
import { DisplayValue } from "@swo/design-system/utils";

import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatDate } from "~shared/hooks/useFormatDate";
import { getPropertyValue } from "~shared/utils/PropertiesUtils";

export function AWSDataSourceProperties({ entity }: { readonly entity: DatasourceDetailRead }) {
  const formatDate = useFormatDate();
  const tSharedDetails = useFixedT("shared:details");

  const tProperties = useFixedT("datasource:details:properties");
  const authenticationType = getPropertyValue(entity, "authentication_type") as string;
  const accountType = getPropertyValue(entity, "account_type");
  const exportType = getPropertyValue(entity, "export_type");
  const tAccountType = useFixedT("datasource:details:accountType");
  const tAuthenticationType = useFixedT("datasource:details:authenticationType");
  const tAwsExportType = useFixedT("datasource:details:awsExportType");
  const tEDPDiscount = useFixedT("datasource:details:edpDiscount");

  return (
    <>
      <CardSection title={tSharedDetails("properties")}>
        <InPageHighlight direction="horizontal" style="block">
          <InPageHighlight.Item title={tProperties("connected_at")}>
            <BoldText color="grey-5">
              {entity?.details?.connected_at && (
                <DisplayValue value={formatDate(entity?.details?.connected_at)} />
              )}
            </BoldText>
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("account_id")}>
            <BoldText color="grey-5">
              <DisplayValue value={getPropertyValue(entity, "account_id")} />
            </BoldText>
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("account_type")}>
            <BoldText color="grey-5">
              <DisplayValue value={tAccountType(accountType as string)} />
            </BoldText>
          </InPageHighlight.Item>
        </InPageHighlight>
      </CardSection>
      <CardSection title={tSharedDetails("authentication")}>
        <InPageHighlight direction="horizontal" style="block">
          <InPageHighlight.Item title={tProperties("authentication_type")}>
            <BoldText color="grey-5">
              <DisplayValue value={tAuthenticationType(authenticationType)} />
            </BoldText>
          </InPageHighlight.Item>
          {authenticationType === "assumed_role" && (
            <InPageHighlight.Item title={tProperties("assumed_role_name")}>
              <BoldText color="grey-5">
                <DisplayValue value={getPropertyValue(entity, "assumed_role_name")} />
              </BoldText>
            </InPageHighlight.Item>
          )}
          {authenticationType === "access_key" && (
            <InPageHighlight.Item title={tProperties("access_key")}>
              <BoldText color="grey-5">
                <DisplayValue value={getPropertyValue(entity, "access_key_id")} />
              </BoldText>
            </InPageHighlight.Item>
          )}
        </InPageHighlight>
      </CardSection>
      {accountType === "management_standalone" && (
        <CardSection title={tSharedDetails("export")}>
          <InPageHighlight direction="horizontal" style="block">
            <InPageHighlight.Item title={tProperties("export_type")}>
              <BoldText color="grey-5">
                <DisplayValue value={exportType && tAwsExportType(exportType as string)} />
              </BoldText>
            </InPageHighlight.Item>
            <InPageHighlight.Item title={tProperties("use_edp_discount")}>
              <BoldText color="grey-5">
                <DisplayValue
                  value={
                    getPropertyValue(entity, "use_edp_discount")
                      ? tEDPDiscount("yes")
                      : tEDPDiscount("no")
                  }
                />
              </BoldText>
            </InPageHighlight.Item>
            <InPageHighlight.Item title={tProperties("export_name")}>
              <BoldText color="grey-5">
                <DisplayValue value={getPropertyValue(entity, "export_name")} />
              </BoldText>
            </InPageHighlight.Item>
            <InPageHighlight.Item title={tProperties("bucket_name")}>
              <BoldText color="grey-5">
                <DisplayValue value={getPropertyValue(entity, "bucket_name")} />
              </BoldText>
            </InPageHighlight.Item>
            <InPageHighlight.Item title={tProperties("bucket_prefix")}>
              <BoldText color="grey-5">
                <DisplayValue value={getPropertyValue(entity, "bucket_prefix")} />
              </BoldText>
            </InPageHighlight.Item>
            <InPageHighlight.Item title={tProperties("region_name")}>
              <BoldText color="grey-5">
                <DisplayValue value={getPropertyValue(entity, "region_name")} />
              </BoldText>
            </InPageHighlight.Item>
            <InPageHighlight.Item title={tProperties("included_regions")}>
              <BoldText color="grey-5">
                <DisplayValue
                  value={(
                    getPropertyValue(entity, "included_regions") as string[] | undefined
                  )?.join(", ")}
                />
              </BoldText>
            </InPageHighlight.Item>
          </InPageHighlight>
        </CardSection>
      )}
    </>
  );
}
