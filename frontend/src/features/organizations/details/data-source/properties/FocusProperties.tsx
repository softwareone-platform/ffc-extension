import { DatasourceDetailRead } from "~api/ffc-api-model";
import { CardSection } from "~shared/components/CardSection";
import { EntityProperties } from "~shared/components/properties/EntityProperties";
import { useFixedT } from "~shared/hooks/useFixedT";

export function FocusProperties({ entity }: { readonly entity: DatasourceDetailRead }) {
  const tSharedDetails = useFixedT("shared:details");

  return (
    <CardSection title={tSharedDetails("properties")}>
      <EntityProperties
        properties={[
          { label: "connected_at", value: entity?.details?.connected_at, type: "date" },
          { label: "id", value: entity?.id, type: "string" },
        ]}
      ></EntityProperties>
    </CardSection>
  );
}
