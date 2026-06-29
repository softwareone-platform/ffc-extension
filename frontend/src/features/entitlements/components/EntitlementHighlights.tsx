import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { Navigation } from "@swo/design-system/navigation";
import { InPageHighlight } from "@swo/in-page-highlight";

import CustomIcon from "~shared/components/custom-icons/CustomIcon";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useEntitlementsDetailsApi } from "../api";

export function EntitlementHighlights({ entitlementId }: { readonly entitlementId: string }) {
  const { data: entity } = useEntitlementsDetailsApi(entitlementId);
  const tProperties = useFixedT("shared:grid:columns");

  return (
    <Navigation.Highlights>
      {entity?.id && (
        <InPageHighlight style="inline">
          <InPageHighlight.Item title={tProperties("affiliate_external_id")}>
            <EntityReferenceCell
              primaryContent={entity.owner.name}
              secondaryContent={entity.owner.id}
              icon={<CustomIcon name={entity.owner.integration} size={44} />}
            />
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("data_source")}>
            {entity.linked_datasource_id && (
              <EntityReferenceCell
                primaryContent={entity.linked_datasource_name as string}
                secondaryContent={entity.linked_datasource_id as string}
                secondaryContentMaxHeight={50}
                icon={<CustomIcon name={entity.linked_datasource_type as string} size={48} />}
              />
            )}
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("organization")}>
            {entity.events.redeemed && (
              <EntityReferenceCell
                primaryContent={entity.events.redeemed?.by.name}
                secondaryContent={entity.events.redeemed?.by.id}
              />
            )}
          </InPageHighlight.Item>
        </InPageHighlight>
      )}
    </Navigation.Highlights>
  );
}
