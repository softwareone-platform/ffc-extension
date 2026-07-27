import { Button } from "@swo/design-system/button";
import { Grid } from "@swo/design-system/grid";

import { EmployeeRead } from "~api/ffc-api-model";
import { CreateUserStandaloneModal } from "~organizations/details/users/modal/CreateUserStandaloneModal";
import { useModalToggle } from "~shared/hooks/useModalToggle";
import { useNotifyParentChildModal } from "~shared/hooks/useNotifyParentChildModal";

import { useGridConfig } from "./UsersGrid.config";

export function UsersGrid({ organizationId }: { organizationId: string }) {
  const { refresh, ...gridProps } = useGridConfig(organizationId);
  const addUserModal = useModalToggle({ onSuccess: refresh });

  useNotifyParentChildModal(addUserModal.isOpen);

  return (
    <>
      <Grid<EmployeeRead> {...gridProps}>
        <Grid.Actions>
            <Button type="primary" onClick={addUserModal.open} testId="add-user-button">
              Add user
            </Button>
        </Grid.Actions>
      </Grid>
      <CreateUserStandaloneModal
        isOpen={addUserModal.isOpen}
        onClose={addUserModal.close}
        className="add-user-modal"
      />
    </>
  );
}
