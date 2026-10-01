import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { Navigation } from "@swo/design-system/navigation";
import { Skeleton } from "@swo/design-system/skeleton";
import { NO_VALUE } from "@swo/design-system/utils";

import CustomIcon from "~shared/components/custom-icons/CustomIcon";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useEntitlementsDetailsApi } from "../api";
import { DataSourceEntityReference } from "./DataSourceEntityReference";

export function EntitlementHighlights({ entitlementId }: { readonly entitlementId: string }) {
  const { data: entity } = useEntitlementsDetailsApi(entitlementId);
  const tProperties = useFixedT("shared:grid:columns");

  return (
    <Navigation.Highlights>
      {entity?.id ? (
        <InPageHighlight style="inline">
          <InPageHighlight.Item title={tProperties("affiliate_external_id")}>
            <EntityReferenceCell
              primaryContent={entity.owner.name}
              secondaryContent={entity.owner.id}
              icon={<CustomIcon name={entity.owner.integration} size={44} />}
            />
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("data_source")}>
            <DataSourceEntityReference entity={entity} />
          </InPageHighlight.Item>
          <InPageHighlight.Item title={tProperties("organization")}>
            {entity.events.redeemed ? (
              <EntityReferenceCell
                primaryContent={entity.events.redeemed?.by.name}
                secondaryContent={entity.events.redeemed?.by.id}
              />
            ) : (
              <>{NO_VALUE}</>
            )}
          </InPageHighlight.Item>
        </InPageHighlight>
      ) : (
        <Skeleton rows={1} cols={1} />
      )}
    </Navigation.Highlights>
  );
}
