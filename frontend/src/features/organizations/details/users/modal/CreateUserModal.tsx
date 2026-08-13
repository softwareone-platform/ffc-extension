import { Modal } from "~shared/components/modal/Modal";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useUserFormController } from "./hooks/useUserFormController";
import { UserFormFields } from "./UserFormFields";

import "./CreateUserModal.scss";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  organizationId: string;
  className?: string;
};

export function CreateUserModal({ isOpen, onClose, organizationId, className }: Readonly<Props>) {
  const tUsers = useFixedT("organization:users");
  const { control, error, isPending, submit, handleCancel } = useUserFormController({
    onClose,
    organizationId,
  });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={tUsers("add_user")}
      className={className}
      onCancel={handleCancel}
      onSubmit={() => submit()}
      submitLabel={tUsers("save")}
      isSubmitting={isPending}
    >
      <form onSubmit={submit}>
        <UserFormFields control={control} error={error} />
      </form>
    </Modal>
  );
}
