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
  const makeUsedAdminModal = useModalToggle<{ employee: Employee; organizationId: string }>({
    onSuccess: refresh,
  });

  useNotifyParentChildModal(addUserModal.isOpen);

  function onAction(action: EmployeeActions, item: Employee) {
    switch (action) {
      case "make_admin":
        makeUsedAdminModal.open({
          employee: item,
          organizationId,
        });
        break;
      default:
        break;
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
        className="add-user-modal"
      />
      <UserMakeAdminModal
        isOpen={makeUsedAdminModal.isOpen}
        onClose={makeUsedAdminModal.close}
        className="make-admin-modal"
        employee={makeUsedAdminModal.data?.employee ?? null}
        organizationId={makeUsedAdminModal.data?.organizationId ?? null}
      />
    </>
  );
}
