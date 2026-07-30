import { Button } from "@swo/design-system/button";
import { Modal } from "@swo/design-system/modal";

import { useUserFormController } from "~organizations/details/users/modal/hooks/useUserFormController";
import { UserFormFields } from "~organizations/details/users/modal/UserFormFields";
import { ModalCloseResult } from "~shared/components/modal/modalEntry";
import { useFixedT } from "~shared/hooks/useFixedT";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  className?: string;
};

export function CreateUserModal({ isOpen, onClose, className }: Readonly<Props>) {
  const tUsers = useFixedT("organization:users");
  const tSharedActions = useFixedT("shared:actions");
  const { control, error, isPending, submit, handleCancel } = useUserFormController({ onClose });

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => onClose()}
      title={tUsers("add_user")}
      width={600}
      className={className}
      actions={
        <>
          <Button type="text" onClick={handleCancel} isDisabled={isPending}>
            {tSharedActions("cancel")}
          </Button>
          <Button type="primary" onClick={() => submit()} isBusy={isPending}>
            {tUsers("save")}
          </Button>
        </>
      }
    >
      <form onSubmit={submit}>
        <UserFormFields control={control} error={error} />
      </form>
    </Modal>
  );
}
