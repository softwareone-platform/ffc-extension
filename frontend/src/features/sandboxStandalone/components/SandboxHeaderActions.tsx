import { useNavigate } from "react-router-dom";

import { useMPTModal } from "@mpt-extension/sdk-react";
import { Button } from "@swo/design-system/button";

import { CreateUserModal } from "~features/sandboxStandalone/modals/CreateUserModal";
import { PATHS } from "~features/sandboxStandalone/paths";
import { useModalToggle } from "~shared/hooks/useModalToggle";

export function SandboxHeaderActions() {
  const navigate = useNavigate();
  const createUser = useModalToggle();
  const { open } = useMPTModal();

  return (
    <>
      <div className="sandbox-standalone__header-action-group">
        <span className="sandbox-standalone__header-action-label">Inside app modal</span>
        <Button type="primary" onClick={() => createUser.open()}>
          Create user
        </Button>
      </div>

      <div className="sandbox-standalone__header-action-group">
        <span className="sandbox-standalone__header-action-label">External entry modal</span>
        <Button
          onClick={() =>
            open("finops.admin.create-entitlement-modal", { context: {}, onClose: () => {} })
          }
        >
          Create entitlement
        </Button>
      </div>

      <div className="sandbox-standalone__header-actions-spacer" aria-hidden="true" />

      <Button type="primary" onClick={() => navigate(PATHS.help)}>
        Help
      </Button>
      <Button type="secondary" onClick={() => navigate(PATHS.termsAndConditions)}>
        Terms & Conditions
      </Button>

      <CreateUserModal isOpen={createUser.isOpen} onClose={createUser.close} />
    </>
  );
}

