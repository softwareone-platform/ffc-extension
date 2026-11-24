import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { EntityProperties } from "~shared/components/properties/EntityProperties";
import { useFixedT } from "~shared/hooks/useFixedT";
import { getPropertyValue } from "~shared/utils/PropertiesUtils";

export function GCPDataSourceProperties({ entity }: { readonly entity: DatasourceDetailRead }) {
  const tSharedDetails = useFixedT("shared:details");

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
              label: "project_id",
              value: getPropertyValue(entity, "project_id"),
              type: "string",
            },
          ]}
        />
      </CardSection>
      <CardSection title={tSharedDetails("billing")}>
        <EntityProperties
          properties={[
            {
              label: "billing_dataset_name",
              value: getPropertyValue(entity, "billing_dataset_name"),
              type: "string",
            },
            {
              label: "billing_table_name",
              value: getPropertyValue(entity, "billing_table_name"),
              type: "string",
            },
            {
              label: "billing_project_id",
              value: getPropertyValue(entity, "billing_project_id"),
              type: "string",
            },
          ]}
        />
      </CardSection>
    </>
  );
}
