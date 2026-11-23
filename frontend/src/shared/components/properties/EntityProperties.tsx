import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { DisplayValue, NO_VALUE } from "@swo/design-system/utils";

import { useFixedT } from "~shared/hooks/useFixedT";
import { useFormatDate } from "~shared/hooks/useFormatDate";

export type EntityReferenceValue = {
  primaryContent?: React.ReactElement | string;
  secondaryContent?: React.ReactElement | string;
  secondaryContentMaxHeight?: number;
  icon?: React.ReactElement;
  testId?: string;
};
type BaseEntityProperty = {
  label: string;
  condition?: boolean;
};

export type EntityProperty =
  | (BaseEntityProperty & {
      value: unknown;
      type: "date" | "string" | "number" | "status" | "boolean" | "raw";
    })
  | (BaseEntityProperty & {
      value: EntityReferenceValue | null | undefined;
      type: "entity";
    });

function PropertyValue({ property }: { readonly property: EntityProperty }) {
  const formatDate = useFormatDate();
  const tBoolean = useFixedT("shared:boolean");

  if (property.value == null || property.value === "") {
    return NO_VALUE;
  }

  switch (property.type) {
    case "boolean":
      if (typeof property.value !== "boolean") {
        return NO_VALUE;
      }
      return tBoolean(property.value ? "yes" : "no");
    case "number":
      return <DisplayValue value={property.value} context="financial" />;
    case "date":
      return typeof property.value === "string" || property.value instanceof Date ? (
        <DisplayValue value={formatDate(property.value)} />
      ) : (
        NO_VALUE
      );
    case "entity":
      return (
        <EntityReferenceCell
          primaryContent={property.value.primaryContent}
          secondaryContent={property.value.secondaryContent || NO_VALUE}
          secondaryContentMaxHeight={property.value.secondaryContentMaxHeight}
          icon={property.value.icon}
          testId={property.value.testId}
        />
      );
    case "raw":
    default:
      return <DisplayValue value={property.value} />;
  }
}

export function EntityProperties({ properties }: { readonly properties: EntityProperty[] }) {
  const tSharedProperties = useFixedT("shared:properties");

  return (
    <InPageHighlight direction="horizontal" style="block">
      {properties
        .filter((property) => property.condition !== false)
        .map((property) => (
          <InPageHighlight.Item key={property.label} title={tSharedProperties(property.label)}>
            <PropertyValue property={property} />
          </InPageHighlight.Item>
        ))}
    </InPageHighlight>
  );
}
