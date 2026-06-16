import { useState } from "react";

import { Button } from "@swo/design-system/button";
import { Grid } from "@swo/design-system/grid";
import { Modal } from "@swo/design-system/modal";
import { EmployeeRead } from "@swo/ffc-api-model";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { useIsStandaloneShell } from "~app/layouts/StandaloneShellContext";
import CreateUserModal from "~features/modal/user/CreateUserModal";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useNotifyParentChildModal } from "~shared/hooks/useNotifyParentChildModal";

import { useGridConfig } from "./UsersGrid.config";

export function UsersGrid({ organizationId }: { organizationId: string }) {
  const { refresh, ...gridProps } = useGridConfig(organizationId);
  const { open } = useMPTModal();
  const tUsers = useFixedT("organization:users");
  const isStandaloneShell = useIsStandaloneShell();
  const [isAddOpen, setIsAddOpen] = useState(false);

  useNotifyParentChildModal(isAddOpen);

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
            <Button
              type="primary"
              onClick={() => setIsAddOpen(true)}
              testId="add-user-button"
            >
              Add user
            </Button>
          ) : (
            <Button onClick={openMptCreateUserModal}>{tUsers("add")}</Button>
          )}
        </Grid.Actions>
      </Grid>
      {isStandaloneShell && (
        <Modal isOpen={isAddOpen} onClose={() => setIsAddOpen(false)} className={"add-user-modal"}>
          <CreateUserModal
            onClose={(result) => {
              setIsAddOpen(false);
              if (result?.success) refresh();
            }}
          />
        </Modal>
      )}
    </>
  );
}
