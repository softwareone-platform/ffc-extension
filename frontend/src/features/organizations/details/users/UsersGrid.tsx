import { Button } from "@swo/design-system/button";
import { Grid } from "@swo/design-system/grid";
import { EmployeeRead } from "@swo/ffc-api-model";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { useIsStandaloneShell } from "~shared/providers/StandaloneShellContext";
import { useModalToggle } from "~features/modal/shared/useModalToggle";
import { CreateUserStandaloneModal } from "~features/modal/user/CreateUserStandaloneModal";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useNotifyParentChildModal } from "~shared/hooks/useNotifyParentChildModal";

import { useGridConfig } from "./UsersGrid.config";

export function UsersGrid({ organizationId }: { organizationId: string }) {
  const { refresh, ...gridProps } = useGridConfig(organizationId);
  const { open } = useMPTModal();
  const tUsers = useFixedT("organization:users");
  const isStandaloneShell = useIsStandaloneShell();
  const addUserModal = useModalToggle({ onSuccess: refresh });

  useNotifyParentChildModal(addUserModal.isOpen);

  const openMptCreateUserModal = () =>
    open("finops.admin.create-user-modal", {
      context: { organizationId },
      onClose: (result) => {
        result.success && refresh();
      },
    });

  return (
    <>
      <Grid<EmployeeRead> {...gridProps}>
        <Grid.Actions>
          {isStandaloneShell ? (
            <Button type="primary" onClick={addUserModal.open} testId="add-user-button">
              Add user
            </Button>
          ) : (
            <Button onClick={openMptCreateUserModal}>{tUsers("add")}</Button>
          )}
        </Grid.Actions>
      </Grid>
      {isStandaloneShell && (
        <CreateUserStandaloneModal
          isOpen={addUserModal.isOpen}
          onClose={addUserModal.close}
          className="add-user-modal"
        />
      )}
    </>
  );
}
