import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalEntryComponent } from "../shared/defineModalEntry";
import { ModalWidget } from "../shared/ModalWidget";
import { UserForm } from "./UserForm";

const CreateUserModal: ModalEntryComponent = ({ onClose }) => {
  const tUsers = useFixedT("organization:users");

  return (
    <ModalWidget title={tUsers("add_user")}>
      <UserForm onClose={onClose} />
    </ModalWidget>
  );
};

export default CreateUserModal;
