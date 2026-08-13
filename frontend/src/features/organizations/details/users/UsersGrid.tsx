import { Button } from "@swo/design-system/button";
import { Grid } from "@swo/design-system/grid";

import { EmployeeRead } from "~api/ffc-api-model";
import { Employee, EmployeeActions } from "~features/organizations/api/model";
import { CreateUserModal } from "~organizations/details/users/modal/CreateUserModal";
import { useModalToggle } from "~shared/hooks/useModalToggle";
import { useNotifyParentChildModal } from "~shared/hooks/useNotifyParentChildModal";

import { UserMakeAdminModal } from "./make-admin-modal/UserMakeAdminModal";
import { useGridConfig } from "./UsersGrid.config";

export function UsersGrid({ organizationId }: { organizationId: string }) {
  const { refresh, ...gridProps } = useGridConfig(organizationId, onAction);
  const addUserModal = useModalToggle({ onSuccess: refresh });
  const makeAdminModal = useModalToggle<{ employee: Employee; organizationId: string }>({
    onSuccess: refresh,
  });

  useNotifyParentChildModal(addUserModal.isOpen);

  function onAction(action: EmployeeActions, item: Employee) {
    if (action === "make_admin") {
      makeAdminModal.open({
        employee: item,
        organizationId,
      });
    }
  }

  return (
    <>
      <Grid<EmployeeRead> {...gridProps}>
        <Grid.Actions>
          <Button type="primary" onClick={addUserModal.open} testId="add-user-button">
            Add user
          </Button>
        </Grid.Actions>
      </Grid>
      <CreateUserModal
        isOpen={addUserModal.isOpen}
        onClose={addUserModal.close}
        organizationId={organizationId}
        className="add-user-modal"
      />
      <UserMakeAdminModal
        isOpen={makeAdminModal.isOpen}
        onClose={makeAdminModal.close}
        className="make-admin-modal"
        employee={makeAdminModal.data?.employee ?? null}
        organizationId={makeAdminModal.data?.organizationId ?? null}
      />
    </>
  );
}
