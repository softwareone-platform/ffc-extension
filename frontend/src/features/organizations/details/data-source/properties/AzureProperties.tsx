import { Link } from "react-router-dom";

import { NO_VALUE } from "@swo/design-system/utils";

import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import DataSourceIcon from "~shared/components/custom-icons/CustomIcon";
import { EntityProperties } from "~shared/components/properties/EntityProperties";
import { useFixedT } from "~shared/hooks/useFixedT";
import { getPropertyValue } from "~shared/utils/PropertiesUtils";

export function AzureDataSourceProperties({ entity }: { readonly entity: DatasourceDetailRead }) {
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
              label: "parent",
              value: entity?.parent?.id
                ? {
                    primaryContent: (
                      <Link to={`../../${entity?.parent?.id}/details`}>{entity?.parent?.name}</Link>
                    ),
                    secondaryContent: entity?.parent?.datasource_id || NO_VALUE,
                    secondaryContentMaxHeight: 50,
                    icon: <DataSourceIcon name={entity?.parent?.type || "unknown"} size={48} />,
                  }
                : null,
              type: "entity",
            },
          ]}
        />
      </CardSection>
      <CardSection title={tSharedDetails("additionalIds")}>
        <EntityProperties
          properties={[
            {
              label: "subscription_id",
              value: getPropertyValue(entity, "subscription_id"),
              type: "string",
            },
            {
              label: "tenant_id",
              value: getPropertyValue(entity, "tenant_id"),
              type: "string",
            },
            {
              label: "client_id",
              value: getPropertyValue(entity, "client_id"),
              type: "string",
            },
          ]}
        />
      </CardSection>
    </>
  );
}
