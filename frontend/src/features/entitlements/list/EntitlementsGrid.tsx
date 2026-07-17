import { Button } from "@swo/design-system/button";
import { Card } from "@swo/design-system/card";
import { Grid } from "@swo/design-system/grid";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { useFixedT } from "~shared/hooks/useFixedT";
import { useModalToggle } from "~shared/hooks/useModalToggle";

import { Entitlement, EntitlementAction } from "../api/model";
import { useGridConfig } from "./EntitlementsGrid.config";
import { TerminateEntitlementModal } from "./terminate-entitlement-modal/TerminateEntitlementModal";

export function EntitlementsGrid() {
  const tProperties = useFixedT("shared:grid:columns");
  const tActions = useFixedT("shared:grid:actions");
  const { refresh, ...gridProps } = useGridConfig(onAction);
  const { open } = useMPTModal();
  const terminateEntitlementModal = useModalToggle<Entitlement>({ onSuccess: refresh });

  function onAction(action: EntitlementAction, item: Entitlement) {
    if (action === "terminate") {
      terminateEntitlementModal.open(item);
    }
  }

  return (
    <>
      <Card testId={"ffc-extension__entitlements-grid"} title={tProperties("entitlements")}>
        <Grid<Entitlement> {...gridProps}>
          <Grid.Actions>
            <Button
              onClick={() =>
                open("finops.admin.create-entitlement-modal", {
                  context: {},
                  onClose: (result) => {
                    result.entitlementCreated && refresh();
                  },
                })
              }
            >
              {tActions("add")}
            </Button>
          </Grid.Actions>
        </Grid>
      </Card>
      <TerminateEntitlementModal
        className="terminate-entitlement-modal"
        entitlement={terminateEntitlementModal.data}
        isOpen={terminateEntitlementModal.isOpen}
        onClose={terminateEntitlementModal.close}
        onSuccess={refresh}
      />
    </>
  );
}
