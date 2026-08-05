import { Card } from "@swo/design-system/card";
import { Grid } from "@swo/design-system/grid";
import { Entity } from "@swo/service";

import { OrganizationRead } from "~api/ffc-api-model";
import type { OrganizationAction } from "~features/organizations/api/model";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useModalToggle } from "~shared/hooks/useModalToggle";

import { EditOrganizationModal } from "./edit-organization-modal/EditOrganizationModal";
import { useGridConfig } from "./OrganizationsGrid.config";

export function OrganizationsGrid() {
  const tProperties = useFixedT("shared:grid:columns");
  const { refresh, ...gridProps } = useGridConfig(onAction);
  const editOrganizationModal = useModalToggle<OrganizationRead>({ onSuccess: refresh });

  function onAction(action: OrganizationAction, item: OrganizationRead) {
    switch (action) {
      case "edit":
        editOrganizationModal.open(item);
        break;
      case "terminate":
        break;
      default:
        break;
    }
  }

  return (
    <>
      <Card testId={"ffc-extension__organizations-grid"} title={tProperties("organizations")}>
        <Grid<Entity<OrganizationRead>> {...gridProps} />
      </Card>
      <EditOrganizationModal
        className="edit-organization-modal"
        organization={editOrganizationModal.data}
        isOpen={editOrganizationModal.isOpen}
        onClose={editOrganizationModal.close}
      />
    </>
  );
}
