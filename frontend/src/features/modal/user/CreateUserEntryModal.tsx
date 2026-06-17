import { Button } from "@swo/design-system/button";

import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalCancelButton } from "../shared/ModalCancelButton";
import { ModalEntryComponent } from "../shared/modalEntry";
import { EntryModalWidget } from "../shared/EntryModalWidget";
import { UserFormFields } from "./UserFormFields";
import { useUserFormController } from "./hooks/useUserFormController";

const CreateUserEntryModal: ModalEntryComponent = ({ onClose }) => {
  const tUsers = useFixedT("organization:users");
  const { control, error, isPending, submit, handleCancel } = useUserFormController({ onClose });

  return (
    <EntryModalWidget title={tUsers("add_user")}>
      <form onSubmit={submit}>
        <UserFormFields control={control} error={error} />
        <div className="modal-actions modal__container">
          <div className="modal-actions__content">
            <ModalCancelButton onClick={handleCancel} isDisabled={isPending} />
            <Button type="primary" htmlType="submit" isBusy={isPending}>
              {tUsers("save")}
            </Button>
          </div>
        </div>
      </form>
    </EntryModalWidget>
  );
};

export default CreateUserEntryModal;
