import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalCloseResult } from "../shared/modalEntry";
import { StandaloneModal } from "../shared/StandaloneModal";
import { useUserFormController } from "./hooks/useUserFormController";
import { UserFormFields } from "./UserFormFields";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  className?: string;
};

export function CreateUserStandaloneModal({ isOpen, onClose, className }: Readonly<Props>) {
  const tUsers = useFixedT("organization:users");
  const { control, error, isPending, submit, handleCancel } = useUserFormController({ onClose });

  return (
    <StandaloneModal
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
    </StandaloneModal>
  );
}
