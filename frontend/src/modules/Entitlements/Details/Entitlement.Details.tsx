import { Card } from "@swo/design-system/card";
import { Link, Navigate, Route, Routes, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { lazy, useMemo } from "react";
import { Navigation } from "@swo/design-system/navigation";
import { Button } from "@swo/design-system/button";
import { EntityReference } from "@swo/design-system/entity-reference";
import { useEntitlementsApi } from "../hooks/useEntitlementsApi";
import { InPageHighlight } from "@swo/design-system/in-page-highlight";
import { useFixedT } from "../../../shared/hooks/useFixedT";
import { EntityReferenceCell } from "@swo/design-system/entity-reference-cell";
import DataSourceIcon from "../../../shared/components/DataSourceIcon";

const EntitlementGeneralDetails = lazy(() =>
  import("./General").then((m) => ({
    default: m.EntitlementGeneralDetails,
  })),
);

export function EntitlementDetails() {
  const { entitlementId } = useParams();
  const { get } = useEntitlementsApi();
  const entityQueryKey = useMemo(
    () => ["Entitlements", "Details", entitlementId],
    ["Entitlements", entitlementId],
  );
  const { data: entity, isLoading } = useQuery({
    queryKey: entityQueryKey,
    queryFn: () => get(entitlementId!),
    select: (res) => res.data,
  });

  const tProperties = useFixedT("shared:grid:columns");

  return (
    <>
      <Card className={"details-header"}>
        {entity && entity.id && (
          <EntityReference
            primaryContent={entity.name}
            secondaryContent={entity.id}
          />
        )}
        <Link to={"/"}>Back</Link>
      </Card>
      <Navigation.Highlights>
        {entity && entity.id && (
          <InPageHighlight style="inline">
            <InPageHighlight.Item title={tProperties("affiliate_external_id")}>
              <EntityReferenceCell
                primaryContent={entity.owner.name}
                secondaryContent={entity.owner.id}
              />
            </InPageHighlight.Item>
            <InPageHighlight.Item title={tProperties("data_source")}>
              {entity.linked_datasource_id && (
                <EntityReferenceCell
                  primaryContent={entity.linked_datasource_name as string}
                  secondaryContent={entity.linked_datasource_id as string}
                  secondaryContentMaxHeight={50}
                  icon={
                    <DataSourceIcon
                      name={entity.linked_datasource_type as string}
                      size={48}
                    />
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
      <Navigation.TopBar
        items={[{ label: "General", path: `/${entity?.id}/general` }]}
      >
        <Navigation.TopBar.Actions>
          <Button>Primary action</Button>
          <Button type="secondary">Button</Button>
        </Navigation.TopBar.Actions>
      </Navigation.TopBar>

      <Card>
        <Routes>
          <Route path="general" index element={<EntitlementGeneralDetails />} />

          <Route path="*" element={<Navigate to={"../general"} replace />} />
        </Routes>
      </Card>
    </>
  );
}
