import { Button } from "@swo/design-system/button";
import { Card } from "@swo/design-system/card";
import { Grid } from "@swo/design-system/grid";

import { useFixedT } from "~shared/hooks/useFixedT";
import { useModalToggle } from "~shared/hooks/useModalToggle";
import { useNotifyParentChildModal } from "~shared/hooks/useNotifyParentChildModal";

import { Entitlement, EntitlementAction } from "../api/model";
import { CreateEntitlementWizard } from "../create-entitlement-wizard/CreateEntitlementWizard";
import { DeleteEntitlementModal } from "./delete-entitlement-modal/DeleteEntitlementModal";
import { useGridConfig } from "./EntitlementsGrid.config";
import { TerminateEntitlementModal } from "./terminate-entitlement-modal/TerminateEntitlementModal";

export function EntitlementsGrid() {
  const tProperties = useFixedT("shared:grid:columns");
  const tActions = useFixedT("shared:grid:actions");
  const { refresh, ...gridProps } = useGridConfig(onAction);
  const createEntitlementModal = useModalToggle({ onSuccess: refresh });
  const terminateEntitlementModal = useModalToggle<Entitlement>({ onSuccess: refresh });
  const deleteEntitlementModal = useModalToggle<Entitlement>({ onSuccess: refresh });

  useNotifyParentChildModal(createEntitlementModal.isOpen);

  function onAction(action: EntitlementAction, item: Entitlement) {
    switch (action) {
      case "delete":
        deleteEntitlementModal.open(item);
        break;
      case "terminate":
        terminateEntitlementModal.open(item);
        break;
      default:
        break;
    }
  }

  return (
    <>
      <Card testId={"ffc-extension__entitlements-grid"} title={tProperties("entitlements")}>
        <Grid<Entitlement> {...gridProps}>
          <Grid.Actions>
            <Button onClick={() => createEntitlementModal.open()}>{tActions("add")}</Button>
          </Grid.Actions>
        </Grid>
      </Card>
      <CreateEntitlementWizard
        isOpen={createEntitlementModal.isOpen}
        onClose={createEntitlementModal.close}
      />
      <TerminateEntitlementModal
        className="terminate-entitlement-modal"
        entitlement={terminateEntitlementModal.data}
        isOpen={terminateEntitlementModal.isOpen}
        onClose={terminateEntitlementModal.close}
        onSuccess={refresh}
      />
      <DeleteEntitlementModal
        className="delete-entitlement-modal"
        entitlement={deleteEntitlementModal.data}
        isOpen={deleteEntitlementModal.isOpen}
        onClose={deleteEntitlementModal.close}
        onSuccess={refresh}
      />
    </>
  );
}
