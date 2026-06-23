import { Outlet, useParams } from "react-router-dom";

import { Card } from "@swo/design-system/card";
import { Navigation } from "@swo/design-system/navigation";

import { SEGMENTS } from "~features/entitlements/paths";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useEntitlementsDetailsApi } from "../api";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import AccountTypeIcon from "~shared/components/account-type-icons/AccountTypeIcon";
import DataSourceIcon from "~shared/components/data-source-icons/DataSourceIcon";

// Inner content for entitlement details. Outer chrome comes from MainLayout
// (standalone) or DetailsLayout (per-feature entry).
export function EntitlementDetailsContent() {
  const tDetails = useFixedT("entitlement:details");

  const topBarItems = [{ label: tDetails("general:title"), path: SEGMENTS.general }];

  const { entitlementId } = useParams();
  const { data: entity } = useEntitlementsDetailsApi(entitlementId);
  const tProperties = useFixedT("shared:grid:columns");

  return (
    <>     
       {/* TODO: Extract to a separate component */}
      <Navigation.Highlights>
        {entity && entity.id && (
          <InPageHighlight style="inline">
            <InPageHighlight.Item title={tProperties("affiliate_external_id")}>
              <EntityReferenceCell
                primaryContent={entity.owner.name}
                secondaryContent={entity.owner.id}
                icon={<AccountTypeIcon name={entity.owner.integration} size={44} />}
              />
            </InPageHighlight.Item>
            <InPageHighlight.Item title={tProperties("data_source")}>
              {entity.linked_datasource_id && (
                <EntityReferenceCell
                  primaryContent={entity.linked_datasource_name as string}
                  secondaryContent={entity.linked_datasource_id as string}
                  secondaryContentMaxHeight={50}
                  icon={
                    <DataSourceIcon name={entity.linked_datasource_type as string} size={48} />
                  }
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
      <Navigation.TopBar items={topBarItems} />
      <Card>
        <Outlet />
      </Card>
    </>
  );
}
