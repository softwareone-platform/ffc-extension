import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { EntityProperties } from "~shared/components/properties/EntityProperties";
import { useFixedT } from "~shared/hooks/useFixedT";
import { getPropertyValue } from "~shared/utils/PropertiesUtils";

export function AWSDataSourceProperties({ entity }: { readonly entity: DatasourceDetailRead }) {
  const tSharedDetails = useFixedT("shared:details");
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
        <EntityProperties
          properties={[
            {
              label: "connected_at",
              value: entity?.details?.connected_at,
              type: "date",
            },
            {
              label: "account_id",
              value: getPropertyValue(entity, "account_id"),
              type: "string",
            },
            {
              label: "account_type",
              value: tAccountType(accountType as string),
              type: "string",
            },
          ]}
        />
      </CardSection>
      <CardSection title={tSharedDetails("authentication")}>
        <EntityProperties
          properties={[
            {
              label: "authentication_type",
              value: tAuthenticationType(authenticationType),
              type: "string",
            },
            {
              label: "assumed_role_name",
              value: getPropertyValue(entity, "assumed_role_name"),
              type: "string",
              condition: authenticationType === "assumed_role",
            },
            {
              label: "access_key",
              value: getPropertyValue(entity, "access_key_id"),
              type: "string",
              condition: authenticationType === "access_key",
            },
          ]}
        />
      </CardSection>
      {accountType === "management_standalone" && (
        <CardSection title={tSharedDetails("export")}>
          <EntityProperties
            properties={[
              {
                label: "export_type",
                value: exportType && tAwsExportType(exportType as string),
                type: "string",
              },
              {
                label: "use_edp_discount",
                value: getPropertyValue(entity, "use_edp_discount")
                  ? tEDPDiscount("yes")
                  : tEDPDiscount("no"),
                type: "string",
              },
              {
                label: "export_name",
                value: getPropertyValue(entity, "export_name"),
                type: "string",
              },
              {
                label: "bucket_name",
                value: getPropertyValue(entity, "bucket_name"),
                type: "string",
              },
              {
                label: "bucket_prefix",
                value: getPropertyValue(entity, "bucket_prefix"),
                type: "string",
              },
              {
                label: "region_name",
                value: getPropertyValue(entity, "region_name"),
                type: "string",
              },
              {
                label: "included_regions",
                value: (getPropertyValue(entity, "included_regions") as string[] | undefined)?.join(
                  ", ",
                ),
                type: "string",
              },
            ]}
          />
        </CardSection>
      )}
    </>
  );
}
